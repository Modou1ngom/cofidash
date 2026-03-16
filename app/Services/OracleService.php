<?php

namespace App\Services;

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
     * Teste la connexion à Oracle
     */
    public function testConnection(): array
    {
        try {
            $response = Http::timeout(30)->get("{$this->pythonServiceUrl}/api/oracle/test");

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('Erreur lors du test de connexion Oracle: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
    }

    /**
     * Récupère la liste des tables Oracle
     */
    public function getTables(): array
    {
        try {
            $response = Http::timeout(30)->get("{$this->pythonServiceUrl}/api/oracle/tables");

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des tables: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
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
            $response = Http::timeout(60)->post("{$this->pythonServiceUrl}/api/oracle/query", [
                'sql' => $sql
            ]);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('Erreur lors de l\'exécution de la requête: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
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
        try {
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

            $response = Http::timeout(120)->get("{$this->pythonServiceUrl}/api/oracle/data/clients", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            Log::error('Erreur API Python Clients', [
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des données clients: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
    }

    /**
     * Récupère les données d'encours épargne depuis Oracle
     */
    public function getEncoursEpargneData(string $period = 'month', ?string $zone = null, ?int $month = null, ?int $year = null, ?string $date = null, string $type = 'epargne-pep-simple'): array
    {
        try {
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

            $response = Http::timeout(120)->get("{$this->pythonServiceUrl}/api/oracle/data/encours", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            Log::error('Erreur API Python Encours Épargne', [
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des données encours épargne: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
    }

    /**
     * Récupère les données de collecte depuis Oracle
     */
    public function getCollectionData(string $period = 'month', ?string $zone = null, ?int $month = null, ?int $year = null, ?string $date = null): array
    {
        try {
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

            $response = Http::timeout(300)->get("{$this->pythonServiceUrl}/api/oracle/data/collection", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            Log::error('Erreur API Python Collection', [
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des données collection: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
    }

    /**
     * Récupère les données de volume DAT depuis Oracle
     */
    public function getVolumeDatData(string $period = 'month', ?string $zone = null, ?int $month = null, ?int $year = null, ?string $date = null): array
    {
        try {
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

            $response = Http::timeout(120)->get("{$this->pythonServiceUrl}/api/oracle/data/volume-dat", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            Log::error('Erreur API Python Volume DAT', [
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des données volume DAT: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
    }

    /**
     * Récupère les données de dépôt de garantie depuis Oracle
     */
    public function getDepotGarantieData(string $period = 'month', ?string $zone = null, ?int $month = null, ?int $year = null, ?string $date = null): array
    {
        try {
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

            $response = Http::timeout(120)->get("{$this->pythonServiceUrl}/api/oracle/data/depot-garantie", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            Log::error('Erreur API Python Dépôt de Garantie', [
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des données dépôt de garantie: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
    }

    /**
     * Récupère les données de production depuis Oracle
     */
    public function getProductionData(string $period = 'month'): array
    {
        try {
            $response = Http::timeout(60)->get("{$this->pythonServiceUrl}/api/oracle/data/production", [
                'period' => $period
            ]);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des données de production: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
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
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
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
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
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
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
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
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
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
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
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
        try {
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

            $response = Http::timeout(300)->get("{$this->pythonServiceUrl}/api/oracle/data/portefeuille-risque", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            Log::error('Erreur API Python Portefeuille Risque', [
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des données portefeuille à risque: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
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
        try {
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

            $response = Http::timeout(300)->get("{$this->pythonServiceUrl}/api/oracle/data/portefeuille-risque-caf", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json(),
                ];
            }

            Log::error('Erreur API Python Portefeuille Risque CAF', [
                'status' => $response->status(),
                'body' => $response->body(),
            ]);

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body(),
            ];
        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des données PAR CAF: ' . $e->getMessage());

            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage(),
            ];
        }
    }

    /**
     * Récupère les données de stock de provision depuis Oracle
     */
    public function getStockProvisionData(?int $month = null, ?int $year = null): array
    {
        try {
            $params = [];
            if ($month) {
                $params['month'] = $month;
            }
            if ($year) {
                $params['year'] = $year;
            }

            $response = Http::timeout(300)->get("{$this->pythonServiceUrl}/api/oracle/data/stock-provision", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            Log::error('Erreur API Python Stock Provision', [
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des données stock provision: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
    }

    /**
     * Récupère les entrées PAR et provisions pour un palier (0, 30, 90, 180, 360)
     */
    public function getEntreesParData(?int $month = null, ?int $year = null, ?int $par = 0): array
    {
        try {
            $params = ['par' => (int) $par];
            if ($month) {
                $params['month'] = $month;
            }
            if ($year) {
                $params['year'] = $year;
            }

            $response = Http::timeout(300)->get("{$this->pythonServiceUrl}/api/oracle/data/entrees-par", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            Log::error('Erreur API Python Entrées PAR', [
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];
        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des données entrées PAR: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
    }

    /**
     * Récupère un GL par code ou recherche par libellé depuis CFSFCUBS145.GLVW_GLMASTER_E
     */
    public function getGlLookup(?string $glCode = null, ?string $glDesc = null): array
    {
        try {
            $params = [];
            if ($glCode) {
                $params['gl_code'] = $glCode;
            }
            if ($glDesc) {
                $params['gl_desc'] = $glDesc;
            }

            $response = Http::timeout(30)->get("{$this->pythonServiceUrl}/api/oracle/data/gl-lookup", $params);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            Log::error('Erreur API Python GL lookup', [
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];
        } catch (\Exception $e) {
            Log::error('Erreur lors du lookup GL: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
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
        try {
            $response = Http::timeout(60)->post("{$this->pythonServiceUrl}/api/oracle/data/cr-par-agence", [
                'date_from' => $dateFrom,
                'date_to' => $dateTo,
                'parent_gl_codes' => $parentGlCodes,
            ]);

            if ($response->successful()) {
                return [
                    'success' => true,
                    'data' => $response->json()
                ];
            }

            Log::error('Erreur API Python CR par Agence', [
                'status' => $response->status(),
                'body' => $response->body()
            ]);

            return [
                'success' => false,
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ];
        } catch (\Exception $e) {
            Log::error('Erreur CR par Agence: ' . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ];
        }
    }
}

