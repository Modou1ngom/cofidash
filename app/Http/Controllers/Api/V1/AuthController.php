<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Services\Vue360\Vue360ApiService;
use App\Services\Vue360\Vue360ScopeService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Storage;
use Illuminate\Validation\ValidationException;

class AuthController extends Controller
{
    public function __construct(
        private readonly Vue360ScopeService $scope,
        private readonly Vue360ApiService $api,
    ) {}

    public function login(Request $request): JsonResponse
    {
        $request->validate([
            'email' => 'required|email',
            'password' => 'required',
        ]);

        $user = User::where('email', $request->email)->first();

        if (!$user || !Hash::check($request->password, $user->password)) {
            throw ValidationException::withMessages([
                'email' => ['Identifiants invalides'],
            ]);
        }

        if (!$user->profile || !$user->profile->is_active) {
            throw ValidationException::withMessages([
                'email' => ['Le profil associé à ce compte est inactif.'],
            ]);
        }

        $token = $user->createToken('vue360-mobile')->plainTextToken;

        return response()->json([
            'token' => $token,
            'user' => $this->scope->formatAuthUser($user),
        ]);
    }

    public function me(Request $request): JsonResponse
    {
        return response()->json([
            'data' => $this->scope->formatAuthUser($request->user()),
        ]);
    }

    public function logout(Request $request): JsonResponse
    {
        if ($request->user()) {
            $request->user()->currentAccessToken()->delete();
        }

        return response()->json(['message' => 'Déconnecté']);
    }

    public function uploadProfilePhoto(Request $request): JsonResponse
    {
        $request->validate([
            'photo' => 'required|image|mimes:jpeg,jpg,png,webp|max:2048',
        ]);

        /** @var User $user */
        $user = $request->user();

        if ($user->profile_photo_path) {
            Storage::disk('public')->delete($user->profile_photo_path);
        }

        $path = $request->file('photo')->store(
            'profile-photos/'.$user->id,
            'public'
        );

        $user->update(['profile_photo_path' => $path]);
        $user->refresh()->loadMissing(['profile', 'territory', 'agency']);

        return response()->json([
            'data' => $this->scope->formatAuthUser($user),
        ]);
    }

    public function deleteProfilePhoto(Request $request): JsonResponse
    {
        /** @var User $user */
        $user = $request->user();

        if ($user->profile_photo_path) {
            Storage::disk('public')->delete($user->profile_photo_path);
            $user->update(['profile_photo_path' => null]);
        }

        $user->refresh()->loadMissing(['profile', 'territory', 'agency']);

        return response()->json([
            'data' => $this->scope->formatAuthUser($user),
        ]);
    }

    public function cafManagers(Request $request): JsonResponse
    {
        /** @var User $user */
        $user = $request->user();

        if ($this->scope->mapRole($user->profile?->code) !== 'caf') {
            return response()->json(['message' => 'Réservé aux chargés d\'affaires'], 403);
        }

        $result = $this->api->cafManagers();
        if (!$result['success']) {
            return response()->json(
                ['message' => $result['message'] ?? 'Impossible de charger les gestionnaires'],
                $result['status'] ?? 500
            );
        }

        return response()->json($result['data']);
    }

    public function changePassword(Request $request): JsonResponse
    {
        $request->validate([
            'current_password' => 'required|string',
            'password' => 'required|string|min:8|confirmed',
        ]);

        /** @var User $user */
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

        $user->refresh()->loadMissing(['profile', 'territory', 'agency']);

        return response()->json([
            'message' => 'Mot de passe modifié avec succès.',
            'data' => $this->scope->formatAuthUser($user),
        ]);
    }

    public function setManagerCode(Request $request): JsonResponse
    {
        /** @var User $user */
        $user = $request->user();

        if ($this->scope->mapRole($user->profile?->code) !== 'caf') {
            return response()->json(['message' => 'Réservé aux chargés d\'affaires'], 403);
        }

        $validated = $request->validate([
            'manager_code' => 'required|string|max:32',
        ]);

        $code = trim($validated['manager_code']);
        if (!$this->api->verifyManagerCode($code)) {
            throw ValidationException::withMessages([
                'manager_code' => ['Code gestionnaire invalide ou introuvable dans Flexcube.'],
            ]);
        }

        $user->update(['manager_code' => $code]);
        $user->refresh()->loadMissing(['profile', 'territory', 'agency']);

        return response()->json([
            'data' => $this->scope->formatAuthUser($user),
        ]);
    }
}
