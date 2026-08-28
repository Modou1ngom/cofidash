<?php

namespace App\Http\Controllers;

use App\Models\Profile;
use Illuminate\Http\Request;
use Illuminate\Validation\Rule;

class ProfileController extends Controller
{
    public function index()
    {
        $profiles = Profile::all();
        return response()->json($profiles);
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'code' => 'required|string|unique:profiles,code|max:50',
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
            'permissions' => 'nullable|array',
            'permissions.*' => 'string',
            'is_active' => 'boolean'
        ]);

        $validated['permissions'] = Profile::normalizePermissions($validated['permissions'] ?? []);
        $profile = Profile::create($validated);

        return response()->json($profile, 201);
    }

    public function show(Profile $profile)
    {
        return response()->json($profile);
    }

    public function update(Request $request, Profile $profile)
    {
        $validated = $request->validate([
            'code' => ['required', 'string', 'max:50', Rule::unique('profiles')->ignore($profile->id)],
            'name' => 'required|string|max:255',
            'description' => 'nullable|string',
            'permissions' => 'nullable|array',
            'permissions.*' => 'string',
            'is_active' => 'boolean'
        ]);

        $validated['permissions'] = Profile::normalizePermissions($validated['permissions'] ?? []);
        $profile->update($validated);

        return response()->json($profile);
    }

    public function destroy(Profile $profile)
    {
        // Vérifier si des utilisateurs utilisent ce profil
        if ($profile->users()->count() > 0) {
            return response()->json([
                'message' => 'Impossible de supprimer ce profil car il est utilisé par des utilisateurs.'
            ], 422);
        }

        $profile->delete();

        return response()->json(['message' => 'Profil supprimé avec succès']);
    }
}

