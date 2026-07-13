<?php

namespace Database\Seeders;

use App\Models\Profile;
use Illuminate\Database\Seeder;

class ProfileSeeder extends Seeder
{
    public function run(): void
    {
        $profiles = [
            [
                'code' => 'MD',
                'name' => 'Directeur Général',
                'description' => 'Valide les objectifs fixés par le DGA',
                'permissions' => [
                    'VIEW_DASHBOARD',
                    'VIEW_CLIENT',
                    'VIEW_ZONES',
                    'VIEW_AGENCIES',
                    'VALIDATE_DGA_OBJECTIVES',
                    'VIEW_FINANCIAL'
                ],
                'is_active' => true
            ],
            [
                'code' => 'DGA',
                'name' => 'Directeur Général Adjoint',
                'description' => 'Fixe les objectifs pour les zones - Doit être validé par le MD',
                'permissions' => [
                    'VIEW_DASHBOARD',
                    'VIEW_CLIENT',
                    'VIEW_ZONES',
                    'VIEW_AGENCIES',
                    'CREATE_ZONE_OBJECTIVES',
                    'VALIDATE_ZONE_OBJECTIVES',
                    'VIEW_FINANCIAL'
                ],
                'is_active' => true
            ],
            [
                'code' => 'RESPONSABLE_ZONE',
                'name' => 'Responsable Zone',
                'description' => 'Fixe les objectifs pour les agences - Doit être validé par le DGA',
                'permissions' => [
                    'VIEW_DASHBOARD',
                    'VIEW_CLIENT',
                    'VIEW_ZONES',
                    'VIEW_AGENCIES',
                    'CREATE_AGENCY_OBJECTIVES',
                    'VALIDATE_AGENCY_OBJECTIVES',
                    'VIEW_FINANCIAL'
                ],
                'is_active' => true
            ],
            [
                'code' => 'CHEF_AGENCE',
                'name' => 'Chef d\'Agence',
                'description' => 'Fixe les objectifs pour ses CAF - Doit être validé par le Responsable Zone',
                'permissions' => [
                    'VIEW_DASHBOARD',
                    'VIEW_CLIENT',
                    'VIEW_ZONES',
                    'VIEW_AGENCIES',
                    'CREATE_CAF_OBJECTIVES',
                    'VIEW_FINANCIAL'
                ],
                'is_active' => true
            ],
            [
                'code' => 'CAF',
                'name' => 'CAF',
                'description' => 'Consultation uniquement - Pas de droits d\'ajout d\'objectifs',
                'permissions' => [
                    'VIEW_DASHBOARD',
                    'VIEW_CLIENT',
                    'VIEW_ZONES',
                    'VIEW_AGENCIES'
                ],
                'is_active' => true
            ],
            [
                'code' => 'CC',
                'name' => 'Conseiller Client',
                'description' => 'Accès à la consultation Client Vue 360°',
                'permissions' => [
                    'VIEW_VUE360',
                    'VIEW_CLIENT'
                ],
                'is_active' => true
            ],
            [
                'code' => 'ADMIN',
                'name' => 'Administrateur',
                'description' => 'Accès complet - Peut tout faire',
                'permissions' => [
                    'VIEW_DASHBOARD',
                    'VIEW_CLIENT',
                    'VIEW_ZONES',
                    'VIEW_AGENCIES',
                    'EDIT_OBJECTIVES',
                    'MODIFY_OBJECTIVES',
                    'VALIDATE_DGA_OBJECTIVES',
                    'VALIDATE_ZONE_OBJECTIVES',
                    'VALIDATE_AGENCY_OBJECTIVES',
                    'MANAGE_FINANCIAL',
                    'VIEW_FINANCIAL',
                    'ADMIN_ACCESS',
                    'MANAGE_USERS',
                    'MANAGE_SETTINGS'
                ],
                'is_active' => true
            ],
            [
                'code' => 'FINANCES',
                'name' => 'Finances',
                'description' => 'Gérer la gestion financière',
                'permissions' => [
                    'VIEW_DASHBOARD',
                    'VIEW_CLIENT',
                    'VIEW_ZONES',
                    'VIEW_AGENCIES',
                    'MANAGE_FINANCIAL',
                    'VIEW_FINANCIAL'
                ],
                'is_active' => true
            ],
            [
                'code' => 'EXPLOITATIONS',
                'name' => 'Exploitations',
                'description' => 'Consultation simple',
                'permissions' => [
                    'VIEW_DASHBOARD',
                    'VIEW_CLIENT',
                    'VIEW_ZONES',
                    'VIEW_AGENCIES'
                ],
                'is_active' => true
            ]
        ];

        foreach ($profiles as $profile) {
            Profile::updateOrCreate(
                ['code' => $profile['code']],
                $profile
            );
        }
    }
}

