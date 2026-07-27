<?php

namespace App\Http\Controllers;

use App\Models\Agency;
use App\Models\User;
use Illuminate\Http\Request;

class AgencyController extends Controller
{
    /**
     * Display a listing of the resource.
     */
    public function index()
    {
        $agencies = Agency::with(['territory', 'chefAgence'])->get();
        return response()->json($agencies);
    }

    /**
     * Store a newly created resource in storage.
     */
    public function store(Request $request)
    {
        $validated = $request->validate([
            'code' => 'required|string|unique:agencies,code',
            'name' => 'required|string',
            'description' => 'nullable|string',
            'territory_id' => 'nullable|exists:territories,id',
            'chef_agence_user_id' => 'nullable|exists:users,id',
        ]);

        $agency = Agency::create($validated);
        return response()->json($agency->load(['territory', 'chefAgence']), 201);
    }

    /**
     * Display the specified resource.
     */
    public function show(string $id)
    {
        $agency = Agency::with(['territory', 'chefAgence', 'users'])->findOrFail($id);
        return response()->json($agency);
    }

    /**
     * Update the specified resource in storage.
     */
    public function update(Request $request, string $id)
    {
        $agency = Agency::findOrFail($id);
        
        $validated = $request->validate([
            'code' => 'sometimes|string|unique:agencies,code,' . $id,
            'name' => 'sometimes|string',
            'description' => 'nullable|string',
            'territory_id' => 'nullable|exists:territories,id',
            'chef_agence_user_id' => 'nullable|exists:users,id',
            'is_active' => 'sometimes|boolean',
        ]);

        $agency->update($validated);
        return response()->json($agency->load(['territory', 'chefAgence']));
    }

    /**
     * Associate a chef d'agence to an agency
     */
    public function assignChefAgence(Request $request, string $id)
    {
        $agency = Agency::findOrFail($id);
        
        $validated = $request->validate([
            'user_id' => 'required|exists:users,id',
        ]);

        $user = User::findOrFail($validated['user_id']);
        
        // Avertissement si l'utilisateur n'a pas le profil CHEF_AGENCE (mais on permet quand même)
        $warning = null;
        if ($user->profile->code !== 'CHEF_AGENCE') {
            $warning = 'Attention: L\'utilisateur sélectionné n\'a pas le profil Chef d\'Agence.';
        }

        $agency->chef_agence_user_id = $validated['user_id'];
        $agency->save();

        $response = response()->json($agency->load('chefAgence'));
        
        if ($warning) {
            $response->header('X-Warning', $warning);
        }
        
        return $response;
    }

    /**
     * Synchronise les agences depuis Oracle
     */
    public function syncFromOracle()
    {
        try {
            $exitCode = \Artisan::call('agencies:sync-from-oracle');
            $output = trim(\Artisan::output());
            $count = Agency::count();

            if ($exitCode !== 0) {
                return response()->json([
                    'success' => false,
                    'message' => 'Échec de la synchronisation des agences depuis Oracle',
                    'output' => $output,
                    'count' => $count,
                ], 500);
            }

            if ($count === 0) {
                return response()->json([
                    'success' => false,
                    'message' => 'Synchronisation terminée mais aucune agence en base. Vérifiez le service Python et Flexcube (STTM_BRANCH).',
                    'output' => $output,
                    'count' => 0,
                ], 502);
            }

            return response()->json([
                'success' => true,
                'message' => "Synchronisation terminée ({$count} agence(s) en base)",
                'output' => $output,
                'count' => $count,
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => 'Erreur lors de la synchronisation: '.$e->getMessage(),
            ], 500);
        }
    }

    /**
     * Remove the specified resource from storage.
     */
    public function destroy(string $id)
    {
        $agency = Agency::findOrFail($id);
        $agency->delete();

        return response()->json(['message' => 'Agence supprimée avec succès']);
    }
}
