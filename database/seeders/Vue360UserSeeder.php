<?php

namespace Database\Seeders;

use App\Models\Agency;
use App\Models\Profile;
use App\Models\Territory;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

/**
 * Comptes de test COFINA CLIENT VUE 360 (spec mobile v1.0).
 * Mot de passe commun : demo1234
 */
class Vue360UserSeeder extends Seeder
{
    public function run(): void
    {
        $password = Hash::make('demo1234');

        $agencyPointE = Agency::where('code', '501')->first();
        $territoryDakar = Territory::where('code', 'DAKAR_VILLE')->first()
            ?? ($agencyPointE?->territory);

        $users = [
            [
                'email' => 'caf@cofina.sn',
                'name' => 'Aminata Diallo',
                'profile' => 'CAF',
                'manager_code' => 'GP-M0856',
                'agency_id' => $agencyPointE?->id,
                'territory_id' => $territoryDakar?->id,
            ],
            [
                'email' => 'chef.agence@cofina.sn',
                'name' => 'Cheikh Ndiaye',
                'profile' => 'CHEF_AGENCE',
                'agency_id' => $agencyPointE?->id,
                'territory_id' => $territoryDakar?->id,
            ],
            [
                'email' => 'responsable.zone@cofina.sn',
                'name' => 'Fatou Sarr',
                'profile' => 'RESPONSABLE_ZONE',
                'agency_id' => null,
                'territory_id' => $territoryDakar?->id,
            ],
            [
                'email' => 'dga@cofina.sn',
                'name' => 'Moussa Ba',
                'profile' => 'DGA',
                'agency_id' => null,
                'territory_id' => null,
            ],
            [
                'email' => 'admin@cofina.sn',
                'name' => 'Admin Cofina',
                'profile' => 'ADMIN',
                'agency_id' => null,
                'territory_id' => null,
            ],
        ];

        foreach ($users as $data) {
            $profile = Profile::where('code', $data['profile'])->first();
            if (!$profile) {
                $this->command?->warn("Profil {$data['profile']} introuvable — ignoré.");
                continue;
            }

            User::updateOrCreate(
                ['email' => $data['email']],
                [
                    'name' => $data['name'],
                    'password' => $password,
                    'profile_id' => $profile->id,
                    'agency_id' => $data['agency_id'],
                    'territory_id' => $data['territory_id'],
                    'manager_code' => $data['manager_code'] ?? null,
                ]
            );
        }

        $this->command?->info('Comptes Vue 360 créés (mot de passe : demo1234)');
    }
}
