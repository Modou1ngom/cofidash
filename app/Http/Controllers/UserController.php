<?php

namespace App\Http\Controllers;

use App\Models\User;
use App\Models\Profile;
use App\Services\Vue360\Vue360ApiService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rule;
use Illuminate\Validation\ValidationException;

class UserController extends Controller
{
    public function __construct(
        private readonly Vue360ApiService $vue360Api,
    ) {
    }

    public function index(Request $request)
    {
        $query = User::with(['profile', 'territory', 'agency']);
        
        // Filtrer par profil si le paramètre est fourni
        if ($request->has('profile')) {
            $profileCode = $request->input('profile');
            $query->whereHas('profile', function($q) use ($profileCode) {
                $q->where('code', $profileCode);
            });
        }
        
        // Filtrer par agence si le paramètre est fourni (pour CHEF_AGENCE qui veut voir ses CAF)
        if ($request->has('agency_id')) {
            $agencyId = $request->input('agency_id');
            $query->where('agency_id', $agencyId);
        }
        
        $users = $query->get();
        return response()->json($users);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:users,email',
            'password' => 'required|string|min:8',
            'profile_id' => 'required|exists:profiles,id',
            'territory_id' => 'nullable|exists:territories,id',
            'agency_id' => 'nullable|exists:agencies,id',
            'manager_code' => 'nullable|string|max:32',
        ]);

        $validated = $this->applyManagerCodeRules($validated);

        $validated['password'] = Hash::make($validated['password']);
        $validated['must_change_password'] = true;

        $user = User::create($validated);

        return response()->json($user->load(['profile', 'territory', 'agency']), 201);
    }

    public function show(User $user)
    {
        return response()->json($user->load('profile'));
    }

    public function update(Request $request, User $user)
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'email' => ['required', 'email', Rule::unique('users')->ignore($user->id)],
            'password' => 'nullable|string|min:8',
            'profile_id' => 'required|exists:profiles,id',
            'territory_id' => 'nullable|exists:territories,id',
            'agency_id' => 'nullable|exists:agencies,id',
            'manager_code' => 'nullable|string|max:32',
        ]);

        $validated = $this->applyManagerCodeRules($validated);

        if (isset($validated['password'])) {
            $validated['password'] = Hash::make($validated['password']);
            $validated['must_change_password'] = true;
        } else {
            unset($validated['password']);
        }

        $user->update($validated);

        return response()->json($user->load(['profile', 'territory', 'agency']));
    }

    public function destroy(User $user)
    {
        $user->delete();

        return response()->json(['message' => 'Utilisateur supprimé avec succès']);
    }

    /**
     * Pour un profil CAF, le code GP (manager_code) est obligatoire et vérifié dans Flexcube.
     * Pour les autres profils, le code est effacé.
     *
     * @param  array<string, mixed>  $validated
     * @return array<string, mixed>
     */
    private function applyManagerCodeRules(array $validated): array
    {
        $profile = Profile::query()->find($validated['profile_id']);
        $isCaf = $profile?->code === 'CAF';

        if (!$isCaf) {
            $validated['manager_code'] = null;

            return $validated;
        }

        $code = trim((string) ($validated['manager_code'] ?? ''));
        if ($code === '') {
            throw ValidationException::withMessages([
                'manager_code' => ['Le code gestionnaire (GP) est obligatoire pour un chargé d\'affaires.'],
            ]);
        }

        if (!$this->vue360Api->verifyManagerCode($code)) {
            throw ValidationException::withMessages([
                'manager_code' => ['Code gestionnaire invalide ou introuvable dans Flexcube.'],
            ]);
        }

        $validated['manager_code'] = $code;

        return $validated;
    }
}
