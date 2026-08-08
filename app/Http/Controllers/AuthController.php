<?php

namespace App\Http\Controllers;

use App\Models\User;
use App\Models\Profile;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

class AuthController extends Controller
{
    public function login(Request $request)
    {
        $request->validate([
            'email' => 'required|email',
            'password' => 'required'
        ]);

        $user = User::where('email', $request->email)->first();

        if (!$user || !Hash::check($request->password, $user->password)) {
            throw ValidationException::withMessages([
                'email' => ['Les identifiants sont incorrects.'],
            ]);
        }

        // Vérifier que le profil est actif
        if (!$user->profile || !$user->profile->is_active) {
            throw ValidationException::withMessages([
                'email' => ['Le profil associé à ce compte est inactif.'],
            ]);
        }

        // Créer le token Sanctum (pas besoin de Auth::login() pour les API)
        $token = $user->createToken('auth-token')->plainTextToken;

        return response()->json([
            'user' => $user->load(['profile', 'territory', 'agency']),
            'token' => $token
        ]);
    }

    public function logout(Request $request)
    {
        if ($request->user()) {
            $request->user()->currentAccessToken()->delete();
        }

        return response()->json(['message' => 'Déconnexion réussie']);
    }

    public function me(Request $request)
    {
        return response()->json($request->user()->load(['profile', 'territory', 'agency']));
    }

    public function changePassword(Request $request)
    {
        $request->validate([
            'current_password' => 'required|string',
            'password' => 'required|string|min:8|confirmed',
        ]);

        $user = $request->user();

        if (!Hash::check($request->current_password, $user->password)) {
            throw ValidationException::withMessages([
                'current_password' => ['Le mot de passe actuel est incorrect.'],
            ]);
        }

        if (Hash::check($request->password, $user->password)) {
            throw ValidationException::withMessages([
                'password' => ['Le nouveau mot de passe doit être différent de l\'actuel.'],
            ]);
        }

        $user->update([
            'password' => $request->password,
            'must_change_password' => false,
        ]);

        return response()->json([
            'message' => 'Mot de passe modifié avec succès.',
            'user' => $user->fresh()->load(['profile', 'territory', 'agency']),
        ]);
    }

    public function getProfiles()
    {
        $profiles = Profile::where('is_active', true)->get();
        return response()->json($profiles);
    }
}

