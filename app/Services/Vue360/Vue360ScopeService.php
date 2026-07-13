<?php

namespace App\Services\Vue360;

use App\Models\Agency;
use App\Models\Territory;
use App\Models\User;
use Illuminate\Support\Facades\Storage;

class Vue360ScopeService
{
    /**
     * Mappe profiles.code vers le rôle attendu par l'app mobile.
     */
    public function mapRole(?string $profileCode): string
    {
        return match (strtoupper((string) $profileCode)) {
            'CAF' => 'caf',
            'CC' => 'cc',
            'CHEF_AGENCE' => 'chef_agence',
            'RESPONSABLE_ZONE' => 'responsable_zone',
            'DGA', 'MD' => 'dga',
            'ADMIN' => 'admin',
            default => 'caf',
        };
    }

    /**
     * Codes agence Oracle (BRANCH_CODE) accessibles selon le rôle.
     * Retourne null = accès réseau complet (pas de filtre).
     *
     * @return array<string>|null
     */
    public function branchCodesForUser(User $user): ?array
    {
        $role = $this->mapRole($user->profile?->code);

        if (in_array($role, ['dga', 'admin'], true)) {
            return null;
        }

        if ($role === 'responsable_zone') {
            $territory = $user->territory ?? $user->responsibleTerritory;
            if (!$territory) {
                return [];
            }

            return Agency::query()
                ->where('territory_id', $territory->id)
                ->where('is_active', true)
                ->pluck('code')
                ->filter()
                ->values()
                ->all();
        }

        if ($role === 'chef_agence') {
            $agency = $user->agency ?? $user->managedAgency;

            return $agency?->code ? [(string) $agency->code] : [];
        }

        // CAF / CC : périmètre agence
        $agency = $user->agency;

        return $agency?->code ? [(string) $agency->code] : [];
    }

    public function branchCodesQueryParam(?array $branchCodes): ?string
    {
        if ($branchCodes === null) {
            return null;
        }

        return implode(',', $branchCodes);
    }

    /**
     * @return array<string, mixed>
     */
    public function formatAuthUser(User $user): array
    {
        $user->loadMissing(['profile', 'territory', 'agency']);

        $profilePhotoUrl = null;
        if ($user->profile_photo_path) {
            $profilePhotoUrl = url(Storage::disk('public')->url($user->profile_photo_path));
        }

        return [
            'id' => 'USR-'.strtoupper($this->mapRole($user->profile?->code)).'-'.$user->id,
            'name' => $user->name,
            'email' => $user->email,
            'role' => $this->mapRole($user->profile?->code),
            'agency' => $user->agency?->name,
            'agency_id' => $user->agency?->code ? 'AG-'.$user->agency->code : null,
            'zone' => $user->territory?->name,
            'zone_id' => $user->territory?->code ? 'ZN-'.$user->territory->code : null,
            'profile_photo_url' => $profilePhotoUrl,
            'manager_code' => $user->manager_code,
        ];
    }
}
