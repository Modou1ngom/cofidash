<?php

namespace App\Services\Vue360;

use App\Models\AppSetting;

class CheckingPiRules
{
    public const SETTING_KEY = 'checking-pi-rules';

    private const SEVERITIES = ['critical', 'optional', 'ignored'];

    /**
     * Catalogue des champs Checking-PI et sévérité par défaut.
     *
     * @return array<int, array{id: string, title: string, fields: array<int, array{key: string, label: string, default: string}>}>
     */
    public static function catalog(): array
    {
        return [
            [
                'id' => 'communes',
                'title' => 'Informations communes',
                'fields' => [
                    ['key' => 'nomClient', 'label' => 'Nom complet', 'default' => 'critical'],
                    ['key' => 'telephoneClient', 'label' => 'Téléphone', 'default' => 'critical'],
                    ['key' => 'emailClient', 'label' => 'Email', 'default' => 'critical'],
                    ['key' => 'numeroCompte', 'label' => 'Numéro de compte', 'default' => 'critical'],
                    ['key' => 'agenceCompte', 'label' => 'Agence', 'default' => 'critical'],
                    ['key' => 'categorieClient', 'label' => 'Type client', 'default' => 'critical'],
                    ['key' => 'typeNumeroCompte', 'label' => 'Statut compte', 'default' => 'critical'],
                    ['key' => 'nationaliteClient', 'label' => 'Nationalité', 'default' => 'critical'],
                    ['key' => 'paysResidenceClient', 'label' => 'Pays de résidence', 'default' => 'critical'],
                    ['key' => 'adresseGeoClient', 'label' => 'Adresse', 'default' => 'critical'],
                    ['key' => 'dateCreation', 'label' => 'Date de création CIF', 'default' => 'critical'],
                    ['key' => 'numeroPieceClient', 'label' => "N° pièce d'identité", 'default' => 'critical'],
                    ['key' => 'typePieceClient', 'label' => 'Type de pièce', 'default' => 'critical'],
                    ['key' => 'photoClient', 'label' => 'Photo client', 'default' => 'critical'],
                ],
            ],
            [
                'id' => 'physique',
                'title' => 'Personne physique',
                'fields' => [
                    ['key' => 'dateNaissanceClient', 'label' => 'Date de naissance', 'default' => 'critical'],
                    ['key' => 'paysNaissanceClient', 'label' => 'Pays de naissance', 'default' => 'optional'],
                    ['key' => 'genreClient', 'label' => 'Genre', 'default' => 'critical'],
                    ['key' => 'nomMere', 'label' => 'Nom de la mère', 'default' => 'critical'],
                ],
            ],
            [
                'id' => 'morale',
                'title' => 'Personne morale',
                'fields' => [
                    ['key' => 'denominationSociale', 'label' => 'Dénomination sociale', 'default' => 'critical'],
                    ['key' => 'raisonSociale', 'label' => 'Raison sociale', 'default' => 'critical'],
                    ['key' => 'identificationRccm', 'label' => 'N° RCCM', 'default' => 'critical'],
                    ['key' => 'identificationFiscale', 'label' => 'Identification fiscale', 'default' => 'optional'],
                    ['key' => 'categorieEntreprise', 'label' => 'Nature juridique', 'default' => 'critical'],
                    ['key' => 'codeActivite', 'label' => "Secteur d'activité", 'default' => 'critical'],
                ],
            ],
        ];
    }

    /**
     * @return array<string, string>
     */
    public static function defaults(): array
    {
        $out = [];
        foreach (self::catalog() as $section) {
            foreach ($section['fields'] as $field) {
                $out[$field['key']] = $field['default'];
            }
        }

        return $out;
    }

    /**
     * @param  array<string, mixed>|null  $value
     * @return array<string, string>
     */
    public static function normalize(?array $value): array
    {
        $defaults = self::defaults();
        $incoming = [];
        if (is_array($value['fields'] ?? null)) {
            $incoming = $value['fields'];
        } elseif (is_array($value)) {
            $incoming = $value;
        }

        $out = $defaults;
        foreach ($incoming as $key => $severity) {
            if (! array_key_exists($key, $defaults)) {
                continue;
            }
            $sev = strtolower(trim((string) $severity));
            if (in_array($sev, self::SEVERITIES, true)) {
                $out[$key] = $sev;
            }
        }

        return $out;
    }

    /**
     * @return array<string, string>
     */
    public static function current(): array
    {
        $setting = AppSetting::query()->where('key', self::SETTING_KEY)->first();

        return self::normalize($setting?->value);
    }

    /**
     * Recalcule le verdict Checking-PI selon les règles enregistrées.
     *
     * @param  array<string, mixed>  $payload
     * @param  array<string, string>|null  $rules
     * @return array<string, mixed>
     */
    public static function apply(array $payload, ?array $rules = null): array
    {
        $rules = $rules ?? self::current();
        $payload['rules'] = $rules;

        if (($payload['reason'] ?? null) === 'no_account') {
            return $payload;
        }

        $sections = [];
        foreach ($payload['sections'] ?? [] as $section) {
            $fields = [];
            foreach ($section['fields'] ?? [] as $field) {
                $key = (string) ($field['key'] ?? '');
                $severity = $rules[$key] ?? 'critical';
                if ($severity === 'ignored') {
                    continue;
                }

                $filled = ($field['status'] ?? '') === 'present' || trim((string) ($field['value'] ?? '')) !== '';
                if ($filled) {
                    $field['status'] = 'present';
                    $field['required'] = $severity === 'critical';
                    $field['badge'] = null;
                } elseif ($severity === 'critical') {
                    $field['status'] = 'critical';
                    $field['required'] = true;
                    $field['display_value'] = 'Manquant (critique)';
                    $field['badge'] = 'Requis pour PI';
                } else {
                    $field['status'] = 'optional';
                    $field['required'] = false;
                    $field['display_value'] = 'Non renseigné';
                    $field['badge'] = 'Recommandé';
                }
                $fields[] = $field;
            }
            if ($fields) {
                $section['fields'] = $fields;
                $sections[] = $section;
            }
        }

        $all = [];
        foreach ($sections as $section) {
            foreach ($section['fields'] as $field) {
                $all[] = $field;
            }
        }

        $present = array_values(array_filter($all, fn ($f) => ($f['status'] ?? '') === 'present'));
        $critical = array_values(array_filter($all, fn ($f) => ($f['status'] ?? '') === 'critical'));
        $optional = array_values(array_filter($all, fn ($f) => ($f['status'] ?? '') === 'optional'));
        $eligible = count($critical) === 0;

        $payload['sections'] = $sections;
        $payload['eligible'] = $eligible;
        $payload['counts'] = [
            'present' => count($present),
            'critical' => count($critical),
            'optional' => count($optional),
        ];
        $payload['missing_critical'] = array_map(
            fn ($f) => [
                'key' => $f['key'],
                'label' => $f['label'],
                'icon' => $f['icon'] ?? '',
                'badge' => $f['badge'] ?? 'Requis pour PI',
            ],
            $critical
        );
        $payload['missing_optional'] = array_map(
            fn ($f) => [
                'key' => $f['key'],
                'label' => $f['label'],
                'icon' => $f['icon'] ?? '',
                'badge' => $f['badge'] ?? 'Recommandé',
            ],
            $optional
        );

        if ($eligible) {
            $payload['verdict'] = 'Le client peut avoir PI';
            $payload['message'] = 'Tous les champs critiques sont renseignés.';
        } else {
            $missing = implode(', ', array_column($critical, 'label'));
            $payload['verdict'] = 'Le client ne peut pas avoir PI';
            $payload['message'] = count($critical).' champ(s) critique(s) manquant(s) : '.$missing.'.';
        }

        return $payload;
    }
}
