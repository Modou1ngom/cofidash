<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Profile extends Model
{
    use HasFactory;

    protected $fillable = [
        'code',
        'name',
        'description',
        'permissions',
        'is_active'
    ];

    protected $casts = [
        'permissions' => 'array',
        'is_active' => 'boolean'
    ];

    public const CATALOG = [
        'VIEW_DASHBOARD',
        'VIEW_CLIENT',
        'VIEW_VUE360',
        'VIEW_ZONES',
        'VIEW_AGENCIES',
        'EDIT_OBJECTIVES',
        'MODIFY_OBJECTIVES',
        'CREATE_ZONE_OBJECTIVES',
        'VALIDATE_ZONE_OBJECTIVES',
        'CREATE_AGENCY_OBJECTIVES',
        'VALIDATE_AGENCY_OBJECTIVES',
        'CREATE_CAF_OBJECTIVES',
        'VALIDATE_DGA_OBJECTIVES',
        'MANAGE_FINANCIAL',
        'VIEW_FINANCIAL',
        'ADMIN_ACCESS',
        'MANAGE_USERS',
        'MANAGE_SETTINGS',
        'MENU_CLIENTS',
        'MENU_CAF_OVERVIEW',
        'MENU_COMPTES_OUVERTS',
        'MENU_COLLECTE_EPARGNE',
        'MENU_PORTEFEUILLE_RISQUE',
        'MENU_NEW_DEAL',
        'MENU_TRANSFERTS',
        'MENU_OBJECTIFS_VIEW',
        'MENU_OBJECTIFS_ADD',
        'MENU_OBJECTIFS_VALIDATE',
        'MENU_GESTION_DONNEES',
        'MENU_GESTION_ENVIRONNEMENTS',
    ];

    public const ALIASES = [
        'view_dashboard' => 'VIEW_DASHBOARD',
        'view_client' => 'VIEW_CLIENT',
        'view_vue360' => 'VIEW_VUE360',
        'view_zones' => 'VIEW_ZONES',
        'view_agencies' => 'VIEW_AGENCIES',
        'view_financial' => 'VIEW_FINANCIAL',
        'edit_objectives' => 'EDIT_OBJECTIVES',
        'modify_objectives' => 'MODIFY_OBJECTIVES',
        'manage_users' => 'MANAGE_USERS',
        'manage_settings' => 'MANAGE_SETTINGS',
        'manage_financial' => 'MANAGE_FINANCIAL',
        'admin_access' => 'ADMIN_ACCESS',
        'menu_clients' => 'MENU_CLIENTS',
        'menu_caf_overview' => 'MENU_CAF_OVERVIEW',
        'menu_comptes_ouverts' => 'MENU_COMPTES_OUVERTS',
        'menu_collecte_epargne' => 'MENU_COLLECTE_EPARGNE',
        'menu_portefeuille_risque' => 'MENU_PORTEFEUILLE_RISQUE',
        'menu_new_deal' => 'MENU_NEW_DEAL',
        'menu_transferts' => 'MENU_TRANSFERTS',
        'menu_objectifs_view' => 'MENU_OBJECTIFS_VIEW',
        'menu_objectifs_add' => 'MENU_OBJECTIFS_ADD',
        'menu_objectifs_validate' => 'MENU_OBJECTIFS_VALIDATE',
        'menu_gestion_donnees' => 'MENU_GESTION_DONNEES',
        'menu_gestion_environnements' => 'MENU_GESTION_ENVIRONNEMENTS',
    ];

    public const CAF_PERMISSIONS = [
        'VIEW_DASHBOARD',
        'VIEW_CLIENT',
        'VIEW_VUE360',
        'VIEW_ZONES',
        'VIEW_AGENCIES',
        'MENU_CAF_OVERVIEW',
        'MENU_COMPTES_OUVERTS',
        'MENU_COLLECTE_EPARGNE',
        'MENU_PORTEFEUILLE_RISQUE',
        'MENU_NEW_DEAL',
        'MENU_TRANSFERTS',
        'MENU_OBJECTIFS_VIEW',
    ];

    public static function defaultMenuPermissions(string $code): array
    {
        $code = strtoupper($code);

        if ($code === 'CC') {
            return [];
        }

        $caf = [
            'MENU_CAF_OVERVIEW',
            'MENU_COMPTES_OUVERTS',
            'MENU_COLLECTE_EPARGNE',
            'MENU_PORTEFEUILLE_RISQUE',
            'MENU_NEW_DEAL',
            'MENU_TRANSFERTS',
            'MENU_OBJECTIFS_VIEW',
        ];

        if ($code === 'CAF') {
            return $caf;
        }

        $operational = [
            'MENU_CLIENTS',
            'MENU_CAF_OVERVIEW',
            'MENU_COMPTES_OUVERTS',
            'MENU_COLLECTE_EPARGNE',
            'MENU_PORTEFEUILLE_RISQUE',
            'MENU_NEW_DEAL',
            'MENU_TRANSFERTS',
        ];

        if ($code === 'MD') {
            return array_merge($operational, ['MENU_OBJECTIFS_VALIDATE']);
        }

        if ($code === 'ADMIN') {
            return array_merge($operational, [
                'MENU_OBJECTIFS_VIEW',
                'MENU_OBJECTIFS_ADD',
                'MENU_OBJECTIFS_VALIDATE',
                'MENU_GESTION_DONNEES',
                'MENU_GESTION_ENVIRONNEMENTS',
            ]);
        }

        return array_merge($operational, [
            'MENU_OBJECTIFS_ADD',
            'MENU_OBJECTIFS_VALIDATE',
        ]);
    }

    public function users(): HasMany
    {
        return $this->hasMany(User::class);
    }

    public static function normalizePermissions(?array $permissions): array
    {
        $normalized = [];
        foreach ($permissions ?? [] as $permission) {
            if (!is_string($permission) || trim($permission) === '') {
                continue;
            }
            $raw = trim($permission);
            $canonical = self::ALIASES[strtolower($raw)] ?? strtoupper($raw);
            if (!in_array($canonical, $normalized, true)) {
                $normalized[] = $canonical;
            }
        }

        return $normalized;
    }
}

