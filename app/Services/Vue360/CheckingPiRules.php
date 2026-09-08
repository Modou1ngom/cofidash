<?php

namespace App\Services\Vue360;

use App\Models\AppSetting;

class CheckingPiRules
{
    public const SETTING_KEY = 'checking-pi-rules';

    public const RULES_VERSION = 2;

    private const SEVERITIES = ['critical', 'optional', 'conditional', 'ignored'];

    /**
     * @return array<int, array{id: string, title: string, fields: array<int, array<string, mixed>>}>
     */
    public static function catalog(): array
    {
        return [
            [
                'id' => 'alias',
                'title' => 'Alias PI',
                'fields' => [
                    [
                        'key' => 'typeAlias',
                        'label' => 'Type d’alias',
                        'icon' => 'badge',
                        'default' => 'critical',
                        'condition_label' => 'S = identifiant BCEAO, M = mobile, C = marchand',
                    ],
                    [
                        'key' => 'valeurAlias',
                        'label' => 'Valeur de l’alias',
                        'icon' => 'hash',
                        'default' => 'conditional',
                        'condition' => 'alias_mc',
                        'condition_label' => 'Obligatoire si typeAlias = M ou C',
                    ],
                ],
            ],
            [
                'id' => 'communes',
                'title' => 'Informations communes',
                'fields' => [
                    ['key' => 'categorieClient', 'label' => 'Catégorie client', 'icon' => 'users', 'default' => 'critical', 'condition_label' => 'P, B, C ou G'],
                    ['key' => 'nomClient', 'label' => 'Nom complet', 'icon' => 'user', 'default' => 'critical'],
                    ['key' => 'telephoneClient', 'label' => 'Téléphone', 'icon' => 'phone', 'default' => 'critical', 'condition_label' => 'Format international UEMOA'],
                    ['key' => 'nationaliteClient', 'label' => 'Nationalité', 'icon' => 'flag', 'default' => 'critical', 'condition_label' => 'ISO 3166-1 alpha-2'],
                    ['key' => 'paysResidenceClient', 'label' => 'Pays de résidence', 'icon' => 'globe', 'default' => 'critical', 'condition_label' => 'ISO 3166-1 alpha-2'],
                    ['key' => 'photoClient', 'label' => 'Photo client', 'icon' => 'photo', 'default' => 'optional'],
                    ['key' => 'emailClient', 'label' => 'Email', 'icon' => 'mail', 'default' => 'optional'],
                    ['key' => 'adresseGeoClient', 'label' => 'Adresse', 'icon' => 'pin', 'default' => 'optional'],
                    ['key' => 'codePostaleClient', 'label' => 'Code postal', 'icon' => 'hash', 'default' => 'optional'],
                    [
                        'key' => 'villeClient',
                        'label' => 'Ville de résidence',
                        'icon' => 'pin',
                        'default' => 'conditional',
                        'condition' => 'kyc_account',
                        'condition_label' => 'Si type de compte ≠ 4',
                    ],
                    ['key' => 'agenceCompte', 'label' => 'Agence', 'icon' => 'building', 'default' => 'optional'],
                ],
            ],
            [
                'id' => 'compte',
                'title' => 'Compte',
                'fields' => [
                    [
                        'key' => 'typeNumeroCompte',
                        'label' => 'Type de numéro de compte',
                        'icon' => 'status',
                        'default' => 'critical',
                        'condition_label' => 'I = IBAN, O = numéro interne',
                    ],
                    [
                        'key' => 'typeCompteClient',
                        'label' => 'Type de compte',
                        'icon' => 'card',
                        'default' => 'critical',
                        'condition_label' => '1 Courant, 2 Épargne, 3 Transaction, 4 Sans KYC',
                    ],
                    ['key' => 'numeroCompte', 'label' => 'Numéro de compte', 'icon' => 'card', 'default' => 'critical'],
                    ['key' => 'dateOuvertureCompte', 'label' => 'Date d’ouverture du compte', 'icon' => 'calendar', 'default' => 'critical'],
                ],
            ],
            [
                'id' => 'physique',
                'title' => 'Personne physique',
                'fields' => [
                    [
                        'key' => 'genreClient',
                        'label' => 'Genre',
                        'icon' => 'users',
                        'default' => 'conditional',
                        'condition' => 'categorie_natural',
                        'condition_label' => 'Si catégorie P ou C (1 = Homme, 2 = Femme)',
                    ],
                    [
                        'key' => 'dateNaissanceClient',
                        'label' => 'Date de naissance',
                        'icon' => 'calendar',
                        'default' => 'conditional',
                        'condition' => 'kyc_natural',
                        'condition_label' => 'Si P ou C et type de compte ≠ 4',
                    ],
                    [
                        'key' => 'paysNaissanceClient',
                        'label' => 'Pays de naissance',
                        'icon' => 'globe',
                        'default' => 'conditional',
                        'condition' => 'kyc_natural',
                        'condition_label' => 'Si P ou C et type de compte ≠ 4 (ISO 3166-1)',
                    ],
                    [
                        'key' => 'villeNaissanceClient',
                        'label' => 'Ville de naissance',
                        'icon' => 'pin',
                        'default' => 'conditional',
                        'condition' => 'kyc_natural',
                        'condition_label' => 'Si P ou C et type de compte ≠ 4',
                    ],
                    [
                        'key' => 'numeroPieceClient',
                        'label' => "N° pièce d'identité",
                        'icon' => 'id',
                        'default' => 'conditional',
                        'condition' => 'piece_identite',
                        'condition_label' => 'Si (P et type compte ≠ 4) ou C',
                    ],
                    [
                        'key' => 'typePieceClient',
                        'label' => 'Type de pièce',
                        'icon' => 'badge',
                        'default' => 'conditional',
                        'condition' => 'piece_identite',
                        'condition_label' => 'Si (P et type compte ≠ 4) ou C — 1 Passeport, 2 CNI',
                    ],
                    [
                        'key' => 'nomMere',
                        'label' => 'Nom de la mère',
                        'icon' => 'heart',
                        'default' => 'optional',
                        'condition' => 'categorie_natural',
                        'condition_label' => 'Recommandé si catégorie P ou C',
                    ],
                ],
            ],
            [
                'id' => 'morale',
                'title' => 'Personne morale',
                'fields' => [
                    [
                        'key' => 'denominationSociale',
                        'label' => 'Dénomination sociale',
                        'icon' => 'briefcase',
                        'default' => 'conditional',
                        'condition' => 'categorie_legal',
                        'condition_label' => 'Si catégorie B ou G',
                    ],
                    [
                        'key' => 'raisonSociale',
                        'label' => 'Raison sociale',
                        'icon' => 'briefcase',
                        'default' => 'conditional',
                        'condition' => 'categorie_legal',
                        'condition_label' => 'Si catégorie B ou G',
                    ],
                    [
                        'key' => 'identificationFiscale',
                        'label' => 'Identification fiscale',
                        'icon' => 'hash',
                        'default' => 'conditional',
                        'condition' => 'categorie_legal',
                        'condition_label' => 'Si catégorie B ou G',
                    ],
                    [
                        'key' => 'identificationRccm',
                        'label' => 'N° RCCM',
                        'icon' => 'hash',
                        'default' => 'conditional',
                        'condition' => 'categorie_business',
                        'condition_label' => 'Si catégorie C (personne physique commerçante)',
                    ],
                    [
                        'key' => 'categorieEntreprise',
                        'label' => 'Nature juridique',
                        'icon' => 'scale',
                        'default' => 'optional',
                        'condition' => 'categorie_legal',
                        'condition_label' => 'Recommandé si catégorie B ou G',
                    ],
                    [
                        'key' => 'codeActivite',
                        'label' => "Secteur d'activité",
                        'icon' => 'layers',
                        'default' => 'optional',
                        'condition' => 'categorie_legal',
                        'condition_label' => 'Recommandé si catégorie B ou G',
                    ],
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
        if ((int) ($value['version'] ?? 0) < self::RULES_VERSION) {
            return $defaults;
        }

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

        $index = self::fieldIndex($payload);
        $ctx = self::context($payload, $index);
        $payload['client_type'] = $ctx['categorie'];
        $payload['client_type_label'] = self::categorieLabel($ctx['categorie']);

        $sections = [];
        foreach (self::catalog() as $sectionMeta) {
            $fields = [];
            foreach ($sectionMeta['fields'] as $meta) {
                $key = $meta['key'];
                $severity = $rules[$key] ?? $meta['default'];
                if ($severity === 'ignored') {
                    continue;
                }

                $condition = $meta['condition'] ?? null;
                $applies = $condition ? self::conditionApplies($condition, $ctx) : true;
                if (! $applies) {
                    continue;
                }

                $source = $index[$key] ?? ['key' => $key, 'value' => '', 'display_value' => ''];
                $value = trim((string) ($source['value'] ?? ''));
                if ($key === 'categorieClient') {
                    $value = $ctx['categorie'];
                }
                $filled = $value !== '';
                $valid = $filled && self::isValid($key, $value, $ctx);
                $effective = $severity === 'conditional' ? 'critical' : $severity;
                $display = $filled
                    ? (string) ($source['display_value'] ?: $source['value'] ?: $value)
                    : '';
                if ($key === 'categorieClient' && $filled) {
                    $display = self::categorieLabel($ctx['categorie']);
                }

                $field = [
                    'key' => $key,
                    'label' => $meta['label'],
                    'icon' => $meta['icon'] ?? ($source['icon'] ?? '•'),
                    'value' => $valid ? $value : ($filled ? $value : ''),
                    'display_value' => $display,
                    'rule' => $severity,
                    'condition_label' => $meta['condition_label'] ?? null,
                ];

                if ($valid) {
                    $field['status'] = 'present';
                    $field['required'] = $effective === 'critical';
                    $field['badge'] = null;
                } elseif ($effective === 'critical') {
                    $field['status'] = 'critical';
                    $field['required'] = true;
                    $field['display_value'] = $filled ? 'Valeur invalide' : 'Manquant (obligatoire)';
                    $field['badge'] = $severity === 'conditional' ? 'Conditionnel — requis pour PI' : 'Requis pour PI';
                } else {
                    $field['status'] = 'optional';
                    $field['required'] = false;
                    $field['display_value'] = $filled ? 'Valeur invalide' : 'Non renseigné';
                    $field['badge'] = 'Recommandé';
                }

                $fields[] = $field;
            }
            if ($fields) {
                $sections[] = [
                    'id' => $sectionMeta['id'],
                    'title' => $sectionMeta['title'],
                    'fields' => $fields,
                ];
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

        $evaluated = count($present) + count($critical) + count($optional);

        $payload['sections'] = $sections;
        $payload['eligible'] = $eligible;
        $payload['completeness'] = $evaluated > 0 ? (int) round(100 * count($present) / $evaluated) : 0;
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
            $payload['message'] = 'Tous les champs obligatoires (y compris conditionnels applicables) sont renseignés.';
        } else {
            $missing = implode(', ', array_column($critical, 'label'));
            $payload['verdict'] = 'Le client ne peut pas avoir PI';
            $payload['message'] = count($critical).' champ(s) obligatoire(s) manquant(s) : '.$missing.'.';
        }

        return $payload;
    }

    /**
     * @param  array<string, mixed>  $payload
     * @return array<string, array<string, mixed>>
     */
    private static function fieldIndex(array $payload): array
    {
        $index = [];
        foreach ($payload['sections'] ?? [] as $section) {
            foreach ($section['fields'] ?? [] as $field) {
                if (! empty($field['key'])) {
                    $index[$field['key']] = $field;
                }
            }
        }
        foreach ($payload['raw'] ?? [] as $key => $value) {
            if (! isset($index[$key])) {
                $index[$key] = [
                    'key' => $key,
                    'value' => $value,
                    'display_value' => $value,
                ];
            }
        }

        return $index;
    }

    /**
     * @param  array<string, mixed>  $payload
     * @param  array<string, array<string, mixed>>  $index
     * @return array{categorie: string, typeCompte: string, typeAlias: string, typeNumero: string}
     */
    private static function context(array $payload, array $index): array
    {
        $rawCat = strtoupper(trim((string) (
            $index['categorieClient']['value']
            ?? $payload['raw']['categorieClient']
            ?? $payload['client_type']
            ?? ''
        )));
        // Flexcube Cofina : I/P = particulier, C = personne morale → B (spec PI).
        if (in_array($rawCat, ['I', 'P'], true)) {
            $categorie = 'P';
        } elseif ($rawCat === 'C') {
            $categorie = 'B';
        } else {
            $categorie = $rawCat;
        }

        return [
            'categorie' => $categorie,
            'typeCompte' => trim((string) ($index['typeCompteClient']['value'] ?? $payload['raw']['typeCompteClient'] ?? '')),
            'typeAlias' => strtoupper(trim((string) ($index['typeAlias']['value'] ?? $payload['raw']['typeAlias'] ?? ''))),
            'typeNumero' => strtoupper(trim((string) ($index['typeNumeroCompte']['value'] ?? $payload['raw']['typeNumeroCompte'] ?? ''))),
        ];
    }

    /**
     * @param  array{categorie: string, typeCompte: string, typeAlias: string, typeNumero: string}  $ctx
     */
    private static function conditionApplies(string $condition, array $ctx): bool
    {
        $cat = $ctx['categorie'];
        $typeCompte = $ctx['typeCompte'];
        $typeAlias = $ctx['typeAlias'];
        $kyc = $typeCompte !== '4';
        $isLegal = in_array($cat, ['B', 'G'], true);
        $isNatural = in_array($cat, ['P', 'C'], true);

        return match ($condition) {
            'alias_mc' => in_array($typeAlias, ['M', 'C'], true),
            'categorie_legal' => $isLegal,
            'categorie_business' => $cat === 'C',
            'categorie_natural' => $isNatural,
            'kyc_natural' => $isNatural && $kyc,
            'kyc_account' => $kyc,
            'piece_identite' => ($cat === 'P' && $kyc) || $cat === 'C',
            default => true,
        };
    }

    private static function categorieLabel(string $categorie): string
    {
        return match ($categorie) {
            'P' => 'Personne physique',
            'B' => 'Personne morale',
            'C' => 'Personne physique commerçante',
            'G' => 'Entité gouvernementale',
            default => $categorie !== '' ? $categorie : '—',
        };
    }

    /**
     * @param  array{categorie: string, typeCompte: string, typeAlias: string, typeNumero: string}  $ctx
     */
    private static function isValid(string $key, string $value, array $ctx): bool
    {
        $upper = strtoupper($value);

        return match ($key) {
            'typeAlias' => in_array($upper, ['S', 'M', 'C'], true),
            'valeurAlias' => self::validAliasValue($value, $ctx['typeAlias']),
            'categorieClient' => in_array($ctx['categorie'], ['P', 'B', 'C', 'G'], true),
            'nationaliteClient', 'paysResidenceClient', 'paysNaissanceClient' => (bool) preg_match('/^[A-Z]{2}$/', $upper),
            'telephoneClient' => self::validWamuPhone($value),
            'typeNumeroCompte' => in_array($upper, ['I', 'O'], true),
            'typeCompteClient' => in_array($value, ['1', '2', '3', '4'], true),
            'numeroCompte' => $ctx['typeNumero'] !== 'I' || strlen(preg_replace('/\s+/', '', $value) ?? '') === 28,
            'typePieceClient' => in_array($value, ['1', '2'], true),
            'genreClient' => in_array($value, ['1', '2'], true),
            default => true,
        };
    }

    private static function validAliasValue(string $value, string $typeAlias): bool
    {
        if ($typeAlias === 'M') {
            return self::validWamuPhone($value);
        }
        if ($typeAlias === 'C') {
            $len = strlen(trim($value));

            return $len >= 2 && $len <= 10;
        }

        return $value !== '';
    }

    private static function validWamuPhone(string $value): bool
    {
        $digits = preg_replace('/\D+/', '', $value) ?? '';
        foreach (['221', '223', '225', '226', '227', '228', '229', '245'] as $code) {
            if (str_starts_with($digits, $code) && strlen($digits) >= 8) {
                return true;
            }
        }

        return false;
    }
}
