<?php

namespace App\Services;

use App\Support\UserFacingError;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Cache;

class OracleService
{
    /**
     * URL de base du service Python
     */
    private $pythonServiceUrl;

    public function __construct()
    {
        $this->pythonServiceUrl = env('PYTHON_SERVICE_URL', 'http://localhost:8001');
    }

    /**
     * Échec API → message utilisateur + détail technique uniquement dans les logs.
     */
    private function failure(string $label, mixed $technical, string $logPrefix = 'Erreur API Python'): array
    {
        $technicalText = is_string($technical)
            ? $technical
            : (json_encode($technical, JSON_UNESCAPED_UNICODE) ?: '');
        Log::error($logPrefix.' ['.$label.']', ['detail' => $technicalText]);

        return [
            'success' => false,
            'error' => 'Service temporairement indisponible',
            'message' => UserFacingError::from($technical),
        ];
    }

    /**
     * Client HTTP vers le service Python : aucune limite de durée (timeout / connect_timeout = 0).
     */
    protected function pythonHttp()
    {
        return Http::timeout(0)->connectTimeout(0);
    }

    /**
     * Normalise les paramètres pour une clé de cache stable.
     */
    protected function normalizeParamsForCache(array $params): array
    {
        return \Illuminate\Support\Arr::sortRecursive($params);
    }

    /**
     * Met en cache les réponses réussies des lectures vers le service Python (moins d'appels Oracle).
     * TTL : ORACLE_DATA_CACHE_TTL (secondes), défaut 300. Mettre 0 pour désactiver.
     */
    protected function rememberSuccessfulRead(string $name, array $params, \Closure $fetch): array
    {
        $ttl = (int) env('ORACLE_DATA_CACHE_TTL', 300);
        if ($ttl <= 0) {
            return $fetch();
        }

        $params = $this->normalizeParamsForCache($params);
        $userId = function_exists('auth') && auth()->check() ? (string) auth()->id() : 'guest';
        $cacheKey = 'oracle_data:'.$userId.':'.$name.':'.hash('sha256', json_encode($params, JSON_UNESCAPED_UNICODE));

        $cached = Cache::get($cacheKey);
        if ($cached !== null && is_array($cached) && ($cached['success'] ?? false)) {
            return $cached;
        }

        $result = $fetch();

        if (($result['success'] ?? false) === true) {
            Cache::put($cacheKey, $result, $ttl);
        }

        return $result;
    }

    /**
     * GET JSON vers le service Python avec cache (réponses succès uniquement).
     */
    public function getPythonGetCached(string $cacheName, string $path, array $params, ?string $logContext = null): array
    {
        $label = $logContext ?? $cacheName;

        return $this->rememberSuccessfulRead($cacheName, $params, function () use ($path, $params, $label) {
            try {
                $response = $this->pythonHttp()->get("{$this->pythonServiceUrl}{$path}", $params);

                if ($response->successful()) {
                    return [
                        'success' => true,
                        'data' => $response->json(),
                    ];
                }

                return $this->failure($label, $response->body());
            } catch (\Exception $e) {
                return $this->failure($label, $e->getMessage(), 'Erreur HTTP Python');
            }
        });
    }

    /**
     * POST JSON vers le service Python avec cache (réponses succès uniquement).
     */
    public function getPythonPostCached(string $cacheName, string $path, array $body, ?string $logContext = null): array
    {
        $label = $logContext ?? $cacheName;

        return $this->rememberSuccessfulRead($cacheName, $body, function () use ($path, $body, $label) {
            try {
                $response = $this->pythonHttp()->post("{$this->pythonServiceUrl}{$path}", $body);

                if ($response->successful()) {
                    return [
                        'success' => true,
                        'data' => $response->json(),
                    ];
                }

                return $this->failure($label, $response->body());
            } catch (\Exception $e) {
                return $this->failure($label, $e->getMessage(), 'Erreur HTTP Python POST');
            }
        });
    }

    /**
     * Teste la connexion à Oracle
     */
    public function testConnection(): array
    {
        try {
            $response = $this->pythonHttp()->get("{$this->pythonServiceUrl}/api/oracle/test");

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            return $this->failure('oracle', $response->body());

        } catch (\Exception $e) {
            Log::error('Erreur lors du test de connexion Oracle: ' . $e->getMessage());
            return $this->failure('oracle', $e->getMessage(), 'Erreur HTTP Python');
        }
    }

    /**
     * Récupère la liste des tables Oracle
     */
    public function getTables(): array
    {
        try {
            $response = $this->pythonHttp()->get("{$this->pythonServiceUrl}/api/oracle/tables");

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            return $this->failure('oracle', $response->body());

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des tables: ' . $e->getMessage());
            return $this->failure('oracle', $e->getMessage(), 'Erreur HTTP Python');
        }
    }

    /**
     * Exécute une requête SQL personnalisée
     */
    public function query(string $sql, array $bindings = []): array
    {
        try {
            // Pour l'instant, on envoie juste la requête SQL
            // TODO: Implémenter le binding de paramètres si nécessaire
            $response = $this->pythonHttp()->post("{$this->pythonServiceUrl}/api/oracle/query", [
                'sql' => $sql
            ]);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            return $this->failure('oracle', $response->body());

        } catch (\Exception $e) {
            Log::error('Erreur lors de l\'exécution de la requête: ' . $e->getMessage());
            return $this->failure('oracle', $e->getMessage(), 'Erreur HTTP Python');
        }
    }

    /**
     * Récupère les données d'une table
     */
    public function table(string $tableName, int $limit = 100, int $offset = 0): array
    {
        $sql = "SELECT * FROM {$tableName}";
        
        if ($limit > 0) {
            $sql .= " FETCH FIRST {$limit} ROWS ONLY";
        }
        
        if ($offset > 0) {
            $sql .= " OFFSET {$offset} ROWS";
        }

        return $this->query($sql);
    }

    /**
     * Récupère les données clients depuis Oracle
     */
    public function getClientsData(string $period = 'month', ?string $zone = null, ?int $month = null, ?int $year = null, ?string $date = null): array
    {
        $params = ['period' => $period];
        if ($zone) {
            $params['zone'] = $zone;
        }
        if ($month) {
            $params['month'] = $month;
        }
        if ($year) {
            $params['year'] = $year;
        }
        if ($date) {
            $params['date'] = $date;
        }

        return $this->getPythonGetCached('clients', '/api/oracle/data/clients', $params, 'Clients');
    }

    /**
     * Récupère les données d'encours épargne depuis Oracle
     */
    public function getEncoursEpargneData(string $period = 'month', ?string $zone = null, ?int $month = null, ?int $year = null, ?string $date = null, string $type = 'epargne-pep-simple'): array
    {
        $params = ['period' => $period, 'type' => $type];
        if ($zone) {
            $params['zone'] = $zone;
        }
        if ($month) {
            $params['month'] = $month;
        }
        if ($year) {
            $params['year'] = $year;
        }
        if ($date) {
            $params['date'] = $date;
        }

        return $this->getPythonGetCached('encours', '/api/oracle/data/encours', $params, 'Encours épargne');
    }

    /**
     * Récupère les données de collecte depuis Oracle
     */
    public function getCollectionData(string $period = 'month', ?string $zone = null, ?int $month = null, ?int $year = null, ?string $date = null): array
    {
        $params = ['period' => $period];
        if ($zone) {
            $params['zone'] = $zone;
        }
        if ($month) {
            $params['month'] = $month;
        }
        if ($year) {
            $params['year'] = $year;
        }
        if ($date) {
            $params['date'] = $date;
        }

        return $this->getPythonGetCached('collection', '/api/oracle/data/collection', $params, 'Collection');
    }

    /**
     * Récupère les données de volume DAT depuis Oracle
     */
    public function getVolumeDatData(string $period = 'month', ?string $zone = null, ?int $month = null, ?int $year = null, ?string $date = null): array
    {
        $params = ['period' => $period];
        if ($zone) {
            $params['zone'] = $zone;
        }
        if ($month) {
            $params['month'] = $month;
        }
        if ($year) {
            $params['year'] = $year;
        }
        if ($date) {
            $params['date'] = $date;
        }

        return $this->getPythonGetCached('volume-dat', '/api/oracle/data/volume-dat', $params, 'Volume DAT');
    }

    /**
     * Récupère les données de dépôt de garantie depuis Oracle
     */
    public function getDepotGarantieData(string $period = 'month', ?string $zone = null, ?int $month = null, ?int $year = null, ?string $date = null): array
    {
        $params = ['period' => $period];
        if ($zone) {
            $params['zone'] = $zone;
        }
        if ($month) {
            $params['month'] = $month;
        }
        if ($year) {
            $params['year'] = $year;
        }
        if ($date) {
            $params['date'] = $date;
        }

        return $this->getPythonGetCached('depot-garantie', '/api/oracle/data/depot-garantie', $params, 'Dépôt de garantie');
    }

    /**
     * Domiciliation de flux (DASH — collecte net)
     */
    public function getDomiciliationFluxData(string $period = 'month', ?string $zone = null, ?int $month = null, ?int $year = null, ?string $date = null): array
    {
        $params = ['period' => $period];
        if ($zone) {
            $params['zone'] = $zone;
        }
        if ($month) {
            $params['month'] = $month;
        }
        if ($year) {
            $params['year'] = $year;
        }
        if ($date) {
            $params['date'] = $date;
        }

        return $this->getPythonGetCached('domiciliation-flux', '/api/oracle/data/domiciliation-flux', $params, 'Domiciliation flux');
    }

    /**
     * Collecte d'épargne à vue (Flexcube — détail client)
     */
    public function getCollecteEpargneAVueData(?int $month = null, ?int $year = null, bool $refresh = false): array
    {
        $params = [];
        if ($month !== null) {
            $params['month'] = $month;
        }
        if ($year !== null) {
            $params['year'] = $year;
        }
        if ($refresh) {
            $params['refresh'] = 1;
        }

        // Lecture directe : le snapshot SQLite Python est déjà rapide (job 06h).
        // Évite un cache Laravel qui masquerait le snapshot du matin.
        return $this->getPythonGetDirect(
            '/api/oracle/data/collecte-epargne-a-vue',
            $params,
            'Collecte épargne à vue'
        );
    }

    /**
     * Force le snapshot quotidien collecte épargne à vue (job 06h).
     */
    public function refreshCollecteEpargneAVueBackup(?int $month = null, ?int $year = null): array
    {
        $params = [];
        if ($month !== null) {
            $params['month'] = $month;
        }
        if ($year !== null) {
            $params['year'] = $year;
        }

        try {
            $query = http_build_query($params);
            $url = "{$this->pythonServiceUrl}/api/oracle/backup/collecte-epargne-a-vue"
                .($query !== '' ? '?'.$query : '');
            $response = $this->pythonHttp()->post($url);
            if ($response->successful()) {
                return ['success' => true, 'data' => $response->json()];
            }

            return $this->failure('Snapshot collecte EPV vue', $response->body());
        } catch (\Exception $e) {
            return $this->failure('Snapshot collecte EPV vue', $e->getMessage(), 'Erreur HTTP Python POST');
        }
    }

    /**
     * Fige les objectifs collecte épargne à vue pour un mois (snapshot SQLite).
     */
    public function refreshObjectifEpvVueBackup(?int $month = null, ?int $year = null): array
    {
        $params = [];
        if ($month !== null) {
            $params['month'] = $month;
        }
        if ($year !== null) {
            $params['year'] = $year;
        }

        try {
            $query = http_build_query($params);
            $url = "{$this->pythonServiceUrl}/api/oracle/backup/objectif-epv-vue"
                .($query !== '' ? '?'.$query : '');
            $response = $this->pythonHttp()->post($url);
            if ($response->successful()) {
                return ['success' => true, 'data' => $response->json()];
            }

            return $this->failure('Snapshot objectifs EPV vue', $response->body());
        } catch (\Exception $e) {
            return $this->failure('Snapshot objectifs EPV vue', $e->getMessage(), 'Erreur HTTP Python POST');
        }
    }

    /**
     * Métadonnées du snapshot objectifs EPV vue.
     */
    public function getObjectifEpvVueSnapshotMeta(?int $month = null, ?int $year = null): array
    {
        $params = [];
        if ($month !== null) {
            $params['month'] = $month;
        }
        if ($year !== null) {
            $params['year'] = $year;
        }

        return $this->getPythonGetCached(
            'objectif-epv-vue-meta',
            '/api/oracle/data/objectif-epv-vue/snapshot',
            $params,
            'Meta objectifs EPV vue'
        );
    }

    /**
     * Transferts d'argent (Orange Money, Wave, Ria, WU) — service Python
     */
    public function getTransfersData(
        string $period = 'month',
        ?int $month = null,
        ?int $year = null,
        ?string $date = null,
        string $service = 'om'
    ): array {
        $params = [
            'period' => $period,
            'service' => $service,
        ];
        if ($month !== null) {
            $params['month'] = $month;
        }
        if ($year !== null) {
            $params['year'] = $year;
        }
        if ($date) {
            $params['date'] = $date;
        }

        // Cache bump si logique snapshot / sources DASH changent (OM, Wave, Ria…)
        return $this->getPythonGetCached('transfers-v4', '/api/oracle/data/transfers', $params, 'Transferts');
    }

    /**
     * Récupère les données de production depuis Oracle
     */
    public function getProductionData(string $period = 'month'): array
    {
        return $this->getPythonGetCached('production-period', '/api/oracle/data/production', [
            'period' => $period,
        ], 'Production');
    }

    /**
     * Utilise la connexion Oracle via DB facade (si configuré)
     * Note: Nécessite l'extension oci8 installée
     */
    public function connection()
    {
        try {
            return \DB::connection('oracle');
        } catch (\Exception $e) {
            Log::error('Impossible d\'utiliser la connexion Oracle directe: ' . $e->getMessage());
            throw new \Exception('Connexion Oracle non disponible. Utilisez le service Python.');
        }
    }

    /**
     * Crée la table OBJECTIFS dans Oracle si elle n'existe pas
     */
    public function createObjectivesTable(): array
    {
        try {
            // Créer la table principale
            $createTableSql = "CREATE TABLE OBJECTIFS (
                ID_OBJECTIF NUMBER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
                TYPE_OBJECTIF VARCHAR2(20) NOT NULL CHECK (TYPE_OBJECTIF IN ('CLIENT', 'PRODUCTION')),
                CATEGORIE VARCHAR2(50) NOT NULL CHECK (CATEGORIE IN ('TERRITOIRE', 'POINT SERVICES', 'GRAND COMPTE')),
                TERRITOIRE VARCHAR2(50),
                CODE_AGENCE VARCHAR2(100) NOT NULL,
                NOM_AGENCE VARCHAR2(200),
                VALEUR NUMBER(15, 2) NOT NULL,
                PERIODE VARCHAR2(20) NOT NULL CHECK (PERIODE IN ('month', 'quarter', 'year')),
                ANNEE NUMBER(4) NOT NULL,
                MOIS NUMBER(2),
                TRIMESTRE NUMBER(1),
                DESCRIPTION VARCHAR2(500),
                DATE_CREATION TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                DATE_MODIFICATION TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )";
            
            $result = $this->query($createTableSql);
            
            if (!$result['success']) {
                // Si la table existe déjà, ce n'est pas grave
                if (stripos($result['message'] ?? '', 'already exists') !== false || 
                    stripos($result['message'] ?? '', 'déjà existe') !== false ||
                    stripos($result['message'] ?? '', 'ORA-00955') !== false) {
                    Log::info('Table OBJECTIFS existe déjà');
                    return [
                        'success' => true,
                        'message' => 'Table OBJECTIFS existe déjà'
                    ];
                }
                return $result;
            }
            
            // Créer les index
            $indexes = [
                "CREATE INDEX IDX_OBJECTIFS_TYPE_ANNEE ON OBJECTIFS(TYPE_OBJECTIF, ANNEE)",
                "CREATE INDEX IDX_OBJECTIFS_CODE_AGENCE ON OBJECTIFS(CODE_AGENCE)",
                "CREATE INDEX IDX_OBJECTIFS_CATEGORIE ON OBJECTIFS(CATEGORIE)",
                "CREATE INDEX IDX_OBJECTIFS_PERIODE ON OBJECTIFS(PERIODE, ANNEE, MOIS, TRIMESTRE)"
            ];
            
            foreach ($indexes as $indexSql) {
                $this->query($indexSql);
                // Ignorer les erreurs si l'index existe déjà
            }
            
            return [
                'success' => true,
                'message' => 'Table OBJECTIFS créée avec succès'
            ];
        } catch (\Exception $e) {
            Log::error('Erreur lors de la création de la table OBJECTIFS: ' . $e->getMessage());
            return $this->failure('oracle', $e->getMessage(), 'Erreur HTTP Python');
        }
    }

    /**
     * Insère un objectif dans Oracle
     */
    public function insertObjective(array $data): array
    {
        try {
            $sql = "INSERT INTO OBJECTIFS (
                TYPE_OBJECTIF, CATEGORIE, TERRITOIRE, CODE_AGENCE, NOM_AGENCE,
                VALEUR, PERIODE, ANNEE, MOIS, TRIMESTRE, DESCRIPTION
            ) VALUES (
                :type, :category, :territory, :agency_code, :agency_name,
                :value, :period, :year, :month, :quarter, :description
            )";
            
            // Pour l'instant, on construit la requête avec les valeurs directement
            // car le service Python ne supporte peut-être pas les bindings
            $sql = str_replace(
                [':type', ':category', ':territory', ':agency_code', ':agency_name', 
                 ':value', ':period', ':year', ':month', ':quarter', ':description'],
                [
                    "'" . addslashes($data['type']) . "'",
                    "'" . addslashes($data['category']) . "'",
                    $data['territory'] ? "'" . addslashes($data['territory']) . "'" : 'NULL',
                    "'" . addslashes($data['agency_code']) . "'",
                    $data['agency_name'] ? "'" . addslashes($data['agency_name']) . "'" : 'NULL',
                    $data['value'],
                    "'" . addslashes($data['period']) . "'",
                    $data['year'],
                    $data['month'] ?? 'NULL',
                    $data['quarter'] ?? 'NULL',
                    $data['description'] ? "'" . addslashes($data['description']) . "'" : 'NULL'
                ],
                $sql
            );
            
            return $this->query($sql);
        } catch (\Exception $e) {
            Log::error('Erreur lors de l\'insertion de l\'objectif: ' . $e->getMessage());
            return $this->failure('oracle', $e->getMessage(), 'Erreur HTTP Python');
        }
    }

    /**
     * Met à jour un objectif dans Oracle
     */
    public function updateObjective(int $id, array $data): array
    {
        try {
            $updates = [];
            if (isset($data['value'])) {
                $updates[] = "VALEUR = " . $data['value'];
            }
            if (isset($data['description'])) {
                $updates[] = "DESCRIPTION = '" . addslashes($data['description']) . "'";
            }
            if (isset($data['agency_name'])) {
                $updates[] = "NOM_AGENCE = '" . addslashes($data['agency_name']) . "'";
            }
            $updates[] = "DATE_MODIFICATION = CURRENT_TIMESTAMP";
            
            $sql = "UPDATE OBJECTIFS SET " . implode(', ', $updates) . " WHERE ID_OBJECTIF = " . $id;
            
            return $this->query($sql);
        } catch (\Exception $e) {
            Log::error('Erreur lors de la mise à jour de l\'objectif: ' . $e->getMessage());
            return $this->failure('oracle', $e->getMessage(), 'Erreur HTTP Python');
        }
    }

    /**
     * Supprime un objectif dans Oracle
     */
    public function deleteObjective(int $id): array
    {
        try {
            $sql = "DELETE FROM OBJECTIFS WHERE ID_OBJECTIF = " . $id;
            return $this->query($sql);
        } catch (\Exception $e) {
            Log::error('Erreur lors de la suppression de l\'objectif: ' . $e->getMessage());
            return $this->failure('oracle', $e->getMessage(), 'Erreur HTTP Python');
        }
    }

    /**
     * Récupère les objectifs depuis Oracle
     */
    public function getObjectives(array $filters = []): array
    {
        try {
            $sql = "SELECT * FROM OBJECTIFS WHERE 1=1";
            
            if (isset($filters['type'])) {
                $sql .= " AND TYPE_OBJECTIF = '" . addslashes($filters['type']) . "'";
            }
            if (isset($filters['category'])) {
                $sql .= " AND CATEGORIE = '" . addslashes($filters['category']) . "'";
            }
            if (isset($filters['year'])) {
                $sql .= " AND ANNEE = " . (int)$filters['year'];
            }
            if (isset($filters['month'])) {
                $sql .= " AND (PERIODE = 'month' AND MOIS = " . (int)$filters['month'] . 
                       " OR PERIODE = 'quarter' OR PERIODE = 'year')";
            }
            if (isset($filters['agency_code'])) {
                $sql .= " AND CODE_AGENCE = '" . addslashes($filters['agency_code']) . "'";
            }
            
            $sql .= " ORDER BY ANNEE DESC, MOIS DESC, TRIMESTRE DESC";
            
            return $this->query($sql);
        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des objectifs: ' . $e->getMessage());
            return $this->failure('oracle', $e->getMessage(), 'Erreur HTTP Python');
        }
    }

    /**
     * Récupère les données de portefeuille à risque depuis Oracle
     *
     * @param  int|null  $month  Mois en cours (1-12)
     * @param  int|null  $year  Année du mois en cours
     * @param  int|null  $monthRef  Mois de référence (1-12), optionnel
     * @param  int|null  $yearRef  Année du mois de référence, optionnel
     */
    public function getPortefeuilleRisqueData(?int $month = null, ?int $year = null, ?int $monthRef = null, ?int $yearRef = null): array
    {
        $params = [];
        if ($month) {
            $params['month'] = $month;
        }
        if ($year) {
            $params['year'] = $year;
        }
        if ($monthRef) {
            $params['month_ref'] = $monthRef;
        }
        if ($yearRef) {
            $params['year_ref'] = $yearRef;
        }

        return $this->getPythonGetCached('portefeuille-risque', '/api/oracle/data/portefeuille-risque', $params, 'Portefeuille risque');
    }

    /**
     * Récupère les données PAR agrégées par CAF pour une agence donnée
     */
    public function getPortefeuilleRisqueCafData(
        ?int $month = null,
        ?int $year = null,
        ?string $agency = null,
        ?int $monthRef = null,
        ?int $yearRef = null
    ): array {
        $params = [];
        if ($month) {
            $params['month'] = $month;
        }
        if ($year) {
            $params['year'] = $year;
        }
        if ($monthRef) {
            $params['month_ref'] = $monthRef;
        }
        if ($yearRef) {
            $params['year_ref'] = $yearRef;
        }
        if ($agency) {
            $params['agency'] = $agency;
        }

        return $this->getPythonGetCached('portefeuille-risque-caf', '/api/oracle/data/portefeuille-risque-caf', $params, 'Portefeuille risque CAF');
    }

    /**
     * Récupère les données de stock de provision depuis Oracle
     */
    public function getStockProvisionData(?int $month = null, ?int $year = null): array
    {
        $params = [];
        if ($month) {
            $params['month'] = $month;
        }
        if ($year) {
            $params['year'] = $year;
        }

        return $this->getPythonGetCached('stock-provision', '/api/oracle/data/stock-provision', $params, 'Stock provision');
    }

    /**
     * Récupère les entrées PAR et provisions pour un palier (0, 30, 90, 180, 360)
     */
    public function getEntreesParData(?int $month = null, ?int $year = null, ?int $par = 0): array
    {
        $params = ['par' => (int) $par];
        if ($month) {
            $params['month'] = $month;
        }
        if ($year) {
            $params['year'] = $year;
        }

        return $this->getPythonGetCached('entrees-par', '/api/oracle/data/entrees-par', $params, 'Entrées PAR');
    }

    /**
     * New Deal : déblocages hors clients NAFA (table SV_DEBLOCAGES_HORS_CLIENT_NAFA).
     */
    public function getNewDealData(?int $limit = null, bool $refresh = false): array
    {
        $params = [];
        if ($limit !== null && $limit > 0) {
            $params['limit'] = $limit;
        }

        if ($refresh) {
            try {
                $response = $this->pythonHttp()->get(
                    "{$this->pythonServiceUrl}/api/oracle/data/new-deal",
                    $params
                );
                if ($response->successful()) {
                    return ['success' => true, 'data' => $response->json()];
                }

                return $this->failure('New Deal', $response->body());
            } catch (\Exception $e) {
                return $this->failure('New Deal', $e->getMessage(), 'Erreur HTTP Python');
            }
        }

        return $this->getPythonGetCached('new-deal', '/api/oracle/data/new-deal', $params, 'New Deal');
    }

    /**
     * Rafraîchit la table source New Deal (DROP + CREATE TABLE AS).
     */
    public function refreshNewDealBackup(): array
    {
        try {
            $response = $this->pythonHttp()->post(
                "{$this->pythonServiceUrl}/api/oracle/backup/new-deal"
            );
            if ($response->successful()) {
                return ['success' => true, 'data' => $response->json()];
            }

            return $this->failure('New Deal backup', $response->body());
        } catch (\Exception $e) {
            return $this->failure('New Deal backup', $e->getMessage(), 'Erreur HTTP Python POST');
        }
    }

    /**
     * Vérifie un PARENT_GL dans DASH_CR_PAR_AGENCE (Cofina) ; pas de libellé renvoyé.
     */
    public function getGlLookup(?string $glCode = null, ?string $glDesc = null): array
    {
        $params = [];
        if ($glCode) {
            $params['gl_code'] = $glCode;
        }
        if ($glDesc) {
            $params['gl_desc'] = $glDesc;
        }

        return $this->getPythonGetCached('gl-lookup', '/api/oracle/data/gl-lookup', $params, 'GL lookup');
    }

    /**
     * Données CR par agence pour une liste de parent GL (sous-rubrique).
     * Requête DATA CR : solde par agence pour la période VALUE_DT.
     *
     * @param string $dateFrom Date début DD/MM/YYYY
     * @param string $dateTo Date fin DD/MM/YYYY
     * @param array $parentGlCodes Liste des codes parent GL
     * @return array { success, data: [{ AC_BRANCH, BRANCH_NAME, montant }] }
     */
    public function getCrParAgenceData(string $dateFrom, string $dateTo, array $parentGlCodes): array
    {
        $body = [
            'date_from' => $dateFrom,
            'date_to' => $dateTo,
            'parent_gl_codes' => $parentGlCodes,
        ];

        return $this->getPythonPostCached('cr-par-agence', '/api/oracle/data/cr-par-agence', $body, 'CR par Agence');
    }

    /**
     * Liste des agences depuis Flexcube STTM_BRANCH (BRANCH_CODE, service Python) pour la synchro Laravel.
     */
    public function getAgenciesFromFlexcube(): array
    {
        return $this->getPythonGetCached(
            'agencies_flexcube_sttm_branch',
            '/api/oracle/data/agencies-from-flexcube',
            [],
            'Agences Flexcube STTM_BRANCH'
        );
    }

    /**
     * @deprecated Utiliser getAgenciesFromFlexcube()
     */
    public function getAgenciesFromDashProductionNombre(): array
    {
        return $this->getAgenciesFromFlexcube();
    }

    /**
     * C360 — synchronise un client Oracle → cache SQLite local.
     */
    public function syncC360Customer(
        string $customerNo,
        int $ecrituresLimit = 10,
        bool $syncRemboursements = true,
        ?array $prets = null
    ): array {
        $body = [
            'customer_no' => $customerNo,
            'ecritures_limit' => $ecrituresLimit,
            'sync_remboursements' => $syncRemboursements,
        ];
        if ($prets !== null) {
            $body['prets'] = $prets;
        }

        return $this->getPythonPostDirect('/api/c360/sync', $body, 'C360 sync');
    }

    /**
     * C360 — vue client (KYC + comptes) depuis le cache local.
     */
    public function getC360Client(string $customerNo, bool $refresh = false, int $ecrituresLimit = 10): array
    {
        return $this->getPythonGetDirect('/api/c360/client/'.$customerNo, [
            'refresh' => $refresh ? 'true' : 'false',
            'ecritures_limit' => $ecrituresLimit,
        ], 'C360 client');
    }

    public function getC360Kyc(string $customerNo, bool $refresh = false): array
    {
        return $this->getPythonGetDirect('/api/c360/kyc/'.$customerNo, [
            'refresh' => $refresh ? 'true' : 'false',
        ], 'C360 KYC');
    }

    public function getC360Comptes(string $customerNo, bool $refresh = false): array
    {
        return $this->getPythonGetDirect('/api/c360/comptes/'.$customerNo, [
            'refresh' => $refresh ? 'true' : 'false',
        ], 'C360 comptes');
    }

    public function getC360Ecritures(string $accountNo, int $limit = 10, bool $refresh = false): array
    {
        return $this->getPythonGetDirect('/api/c360/ecritures/'.$accountNo, [
            'limit' => $limit,
            'refresh' => $refresh ? 'true' : 'false',
        ], 'C360 écritures');
    }

    public function getC360Remboursements(string $noPret, ?string $customerNo = null, bool $refresh = false): array
    {
        $params = ['refresh' => $refresh ? 'true' : 'false'];
        if ($customerNo) {
            $params['customer_no'] = $customerNo;
        }

        return $this->getPythonGetDirect('/api/c360/remboursements/'.$noPret, $params, 'C360 remboursements');
    }

    public function getC360SyncStatus(string $customerNo): array
    {
        return $this->getPythonGetDirect('/api/c360/sync/status/'.$customerNo, [], 'C360 sync status');
    }

    /**
     * GET vers Python sans cache Laravel (données déjà en cache SQLite côté Python).
     */
    protected function getPythonGetDirect(string $path, array $params, string $logContext): array
    {
        try {
            $response = $this->pythonHttp()->get("{$this->pythonServiceUrl}{$path}", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json(),
                ];
            }

            Log::error('Erreur API Python GET ['.$logContext.']', [
                'path' => $path,
                'status' => $response->status(),
                'body' => $response->body(),
            ]);

            return $this->failure($logContext, $response->body());
        } catch (\Exception $e) {
            return $this->failure($logContext, $e->getMessage(), 'Exception API Python GET');
        }
    }

    /**
     * POST vers Python sans cache Laravel.
     */
    protected function getPythonPostDirect(string $path, array $body, string $logContext): array
    {
        try {
            $response = $this->pythonHttp()->post("{$this->pythonServiceUrl}{$path}", $body);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json(),
                ];
            }

            Log::error('Erreur API Python POST ['.$logContext.']', [
                'path' => $path,
                'status' => $response->status(),
                'body' => $response->body(),
            ]);

            return $this->failure($logContext, $response->body());
        } catch (\Exception $e) {
            return $this->failure($logContext, $e->getMessage(), 'Exception API Python POST');
        }
    }
}

