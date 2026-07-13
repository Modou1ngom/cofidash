<?php

namespace App\Http\Controllers;

use App\Models\User;
use App\Models\Profile;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rule;

class UserController extends Controller
{
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

        $validated['password'] = Hash::make($validated['password']);

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

        if (isset($validated['password'])) {
            $validated['password'] = Hash::make($validated['password']);
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
}

