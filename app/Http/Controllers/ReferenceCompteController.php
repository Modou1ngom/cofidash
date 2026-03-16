<?php

namespace App\Http\Controllers;

use App\Models\ReferenceCompteBloc;
use App\Models\ReferenceCompteGl;
use App\Models\ReferenceCompteRubrique;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

class ReferenceCompteController extends Controller
{
    /**
     * Liste tous les blocs avec leurs rubriques et GL.
     */
    public function index(): JsonResponse
    {
        try {
            $blocs = ReferenceCompteBloc::with(['rubriques.gls'])
                ->orderBy('sort_order')
                ->get()
                ->map(function ($bloc) {
                    return [
                        'id' => $bloc->id,
                        'libelle' => $bloc->libelle,
                        'rubriques' => $bloc->rubriques->map(function ($rubrique) {
                            return [
                                'id' => $rubrique->id,
                                'libelle' => $rubrique->libelle,
                                'gls' => $rubrique->gls->map(fn ($gl) => [
                                    'id' => $gl->id,
                                    'numero_gl' => $gl->numero_gl,
                                    'nom_gl' => $gl->nom_gl,
                                ])->values()->all(),
                            ];
                        })->values()->all(),
                    ];
                });

            return response()->json(['data' => $blocs]);
        } catch (\Exception $e) {
            Log::error('ReferenceCompte index: ' . $e->getMessage());
            return response()->json([
                'error' => 'Erreur lors du chargement',
                'message' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Enregistre les blocs, rubriques et GL (remplace tout).
     */
    public function store(Request $request): JsonResponse
    {
        $request->validate([
            'blocs' => 'required|array',
            'blocs.*.libelle' => 'required|string|max:255',
            'blocs.*.rubriques' => 'array',
            'blocs.*.rubriques.*.libelle' => 'required|string|max:255',
            'blocs.*.rubriques.*.gls' => 'array',
            'blocs.*.rubriques.*.gls.*.numero_gl' => 'required|string|max:50',
            'blocs.*.rubriques.*.gls.*.nom_gl' => 'nullable|string',
        ]);

        try {
            DB::transaction(function () use ($request) {
                ReferenceCompteGl::query()->delete();
                ReferenceCompteRubrique::query()->delete();
                ReferenceCompteBloc::query()->delete();

                foreach ($request->input('blocs', []) as $blocOrder => $b) {
                    $bloc = ReferenceCompteBloc::create([
                        'libelle' => $b['libelle'],
                        'sort_order' => $blocOrder,
                    ]);

                    foreach (array_values($b['rubriques'] ?? []) as $rubOrder => $r) {
                        $rubrique = ReferenceCompteRubrique::create([
                            'bloc_id' => $bloc->id,
                            'libelle' => $r['libelle'],
                            'sort_order' => $rubOrder,
                        ]);

                        foreach (array_values($r['gls'] ?? []) as $glOrder => $g) {
                            if (empty($g['numero_gl'])) {
                                continue;
                            }
                            ReferenceCompteGl::create([
                                'rubrique_id' => $rubrique->id,
                                'numero_gl' => $g['numero_gl'],
                                'nom_gl' => $g['nom_gl'] ?? null,
                                'sort_order' => $glOrder,
                            ]);
                        }
                    }
                }
            });

            return response()->json([
                'success' => true,
                'message' => 'Référence compte enregistrée avec succès.',
            ]);
        } catch (\Exception $e) {
            Log::error('ReferenceCompte store: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'error' => 'Erreur lors de l\'enregistrement',
                'message' => $e->getMessage(),
            ], 500);
        }
    }
}
