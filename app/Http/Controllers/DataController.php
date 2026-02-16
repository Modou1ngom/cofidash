<?php

namespace App\Http\Controllers;

use App\Services\OracleService;
use App\Models\Objective;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class DataController extends Controller
{
    /**
     * URL de base du service Python
     */
    private $pythonServiceUrl;
    
    /**
     * Service Oracle
     */
    protected $oracleService;

    public function __construct(OracleService $oracleService)
    {
        $this->pythonServiceUrl = env('PYTHON_SERVICE_URL', 'http://localhost:8001');
        $this->oracleService = $oracleService;
    }

    /**
     * Teste la connexion à Oracle
     */
    public function testOracleConnection(): JsonResponse
    {
        $result = $this->oracleService->testConnection();
        
        if ($result['success']) {
            return response()->json($result['data']);
        }

        return response()->json([
            'error' => $result['error'],
            'message' => $result['message']
        ], 500);
    }

    /**
     * Récupère la liste des tables Oracle
     */
    public function getTables(): JsonResponse
    {
        $result = $this->oracleService->getTables();
        
        if ($result['success']) {
            return response()->json($result['data']);
        }

        return response()->json([
            'error' => $result['error'],
            'message' => $result['message']
        ], 500);
    }

    /**
     * Exécute une requête SQL personnalisée
     */
    public function executeQuery(Request $request): JsonResponse
    {
        $request->validate([
            'sql' => 'required|string'
        ]);

        $result = $this->oracleService->query($request->input('sql'));

        if ($result['success']) {
            return response()->json($result['data']);
        }

        return response()->json([
            'error' => $result['error'],
            'message' => $result['message']
        ], 500);
    }

    /**
     * Récupère les données clients depuis Oracle
     */
    public function getClientsData(Request $request): JsonResponse
    {
        try {
            $period = $request->input('period', 'month');
            $zone = $request->input('zone');
            $month = $request->input('month');
            $year = $request->input('year');
            $date = $request->input('date'); // Pour la période "week"

            $result = $this->oracleService->getClientsData($period, $zone, $month ? (int)$month : null, $year ? (int)$year : null, $date);

            if ($result['success']) {
                $data = $result['data'];
                
                // Les données peuvent être dans $data directement ou dans $data['data']
                $actualData = $data;
                if (isset($data['data']) && is_array($data['data'])) {
                    $actualData = $data['data'];
                }
                
                // Fusionner les objectifs personnalisés avec les données Oracle
                // Utiliser l'année et le mois de la requête, ou les valeurs actuelles
                $mergeYear = $year ? (int)$year : (int)date('Y');
                $mergeMonth = null;
                
                // Déterminer le mois selon la période
                if ($period === 'month' && $month) {
                    $mergeMonth = (int)$month;
                } elseif ($period === 'week' && $date) {
                    // Extraire le mois de la date
                    $dateObj = \DateTime::createFromFormat('Y-m-d', $date);
                    if ($dateObj) {
                        $mergeMonth = (int)$dateObj->format('n');
                    }
                } elseif ($period === 'month') {
                    $mergeMonth = (int)date('n');
                }
                
                Log::info('🔄 Début fusion des objectifs', [
                    'year' => $mergeYear,
                    'month' => $mergeMonth,
                    'period' => $period,
                    'request_year' => $year,
                    'request_month' => $month,
                    'data_structure' => [
                        'has_hierarchicalData' => isset($actualData['hierarchicalData']),
                        'has_territories' => isset($actualData['territories']),
                        'keys' => array_keys($actualData)
                    ]
                ]);
                
                $actualData = $this->mergeObjectivesWithData($actualData, 'CLIENT', $mergeYear, $mergeMonth);
                
                // Remettre les données fusionnées dans la structure originale
                if (isset($data['data'])) {
                    $data['data'] = $actualData;
                } else {
                    $data = $actualData;
                }
                
                Log::info('✅ Données fusionnées retournées au client');
                
                return response()->json($data);
            }

            Log::error('Erreur lors de la récupération des données clients', [
                'error' => $result['error'],
                'message' => $result['message']
            ]);

            return response()->json([
                'error' => $result['error'],
                'message' => $result['message']
            ], 500);
        } catch (\Exception $e) {
            Log::error('Exception lors de la récupération des données clients', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);

            return response()->json([
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Fusionne les objectifs EPARGNE_SIMPLE et EPARGNE_PROJET avec les données Oracle
     * et les additionne pour obtenir l'objectif total
     */
    private function mergeEpargneObjectivesWithData($data, $year, $month = null)
    {
        try {
            // Récupérer tous les objectifs EPARGNE_SIMPLE et EPARGNE_PROJET pour cette période
            $objectivesQuery = Objective::whereIn('type', ['EPARGNE_SIMPLE', 'EPARGNE_PROJET'])
                ->where('year', $year);
            
            if ($month) {
                $objectivesQuery->where(function($q) use ($month) {
                    $q->where(function($q2) use ($month) {
                        $q2->where('period', 'month')->where('month', $month);
                    })
                    ->orWhere('period', 'quarter')
                    ->orWhere('period', 'year');
                });
            } else {
                // Si pas de mois, prendre tous les objectifs de l'année
                $objectivesQuery->where(function($q) {
                    $q->where('period', 'year')
                      ->orWhere('period', 'quarter');
                });
            }
            
            $objectives = $objectivesQuery->get();
            
            Log::info('Objectifs EPARGNE trouvés pour fusion', [
                'count' => $objectives->count(),
                'year' => $year,
                'month' => $month
            ]);
            
            // Grouper les objectifs par agence (code et nom) et additionner EPARGNE_SIMPLE + EPARGNE_PROJET
            $objectivesByAgency = [];
            foreach ($objectives as $objective) {
                $code = strtoupper(trim($objective->agency_code ?? ''));
                $name = strtoupper(trim($objective->agency_name ?? ''));
                $key = $code ?: $name;
                
                if ($key) {
                    if (!isset($objectivesByAgency[$key])) {
                        $objectivesByAgency[$key] = [
                            'code' => $code,
                            'name' => $name,
                            'total' => 0
                        ];
                    }
                    $objectivesByAgency[$key]['total'] += (int)$objective->value;
                }
            }
            
            // Créer des index pour recherche rapide
            $objectivesByCode = [];
            $objectivesByName = [];
            foreach ($objectivesByAgency as $key => $agencyObj) {
                if ($agencyObj['code']) {
                    $objectivesByCode[$agencyObj['code']] = $agencyObj['total'];
                }
                if ($agencyObj['name']) {
                    $objectivesByName[$agencyObj['name']] = $agencyObj['total'];
                }
            }
            
            // Normaliser les noms pour recherche
            $normalizeAgencyName = function($name) {
                $name = strtoupper(trim($name ?? ''));
                $name = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $name);
                $name = preg_replace('/\s+/', ' ', $name);
                return trim($name);
            };
            
            $objectivesByNormalizedCode = [];
            $objectivesByNormalizedName = [];
            foreach ($objectivesByAgency as $key => $agencyObj) {
                $normalizedCode = $normalizeAgencyName($agencyObj['code']);
                $normalizedName = $normalizeAgencyName($agencyObj['name']);
                if ($normalizedCode) {
                    $objectivesByNormalizedCode[$normalizedCode] = $agencyObj['total'];
                }
                if ($normalizedName) {
                    $objectivesByNormalizedName[$normalizedName] = $agencyObj['total'];
                }
            }
            
            $mergedCount = 0;
            
            // Fonction récursive pour fusionner les objectifs dans la structure hiérarchique
            $mergeRecursive = function(&$item, $depth = 0) use (&$mergeRecursive, &$mergedCount, $normalizeAgencyName, $objectivesByCode, $objectivesByName, $objectivesByNormalizedCode, $objectivesByNormalizedName) {
                if (is_array($item)) {
                    foreach ($item as $key => &$value) {
                        if (is_array($value)) {
                            // Extraire tous les champs possibles pour le nom/code d'agence
                            $possibleNames = [
                                $value['name'] ?? null,
                                $value['AGENCE'] ?? null,
                                $value['NOM_AGENCE'] ?? null,
                                $value['NOM'] ?? null,
                                $value['LIBELLE'] ?? null,
                                $value['LIBELLE_AGENCE'] ?? null
                            ];
                            
                            $possibleCodes = [
                                $value['code'] ?? null,
                                $value['CODE_AGENCE'] ?? null,
                                $value['CODE'] ?? null,
                                $value['AGENCE'] ?? null
                            ];
                            
                            $agencyName = '';
                            foreach ($possibleNames as $name) {
                                if (!empty($name)) {
                                    $agencyName = strtoupper(trim($name));
                                    break;
                                }
                            }
                            
                            $agencyCode = '';
                            foreach ($possibleCodes as $code) {
                                if (!empty($code)) {
                                    $agencyCode = strtoupper(trim($code));
                                    break;
                                }
                            }
                            
                            if (empty($agencyCode) && !empty($agencyName)) {
                                $agencyCode = $agencyName;
                            }
                            
                            $normalizedAgencyName = $normalizeAgencyName($agencyName);
                            $normalizedAgencyCode = $normalizeAgencyName($agencyCode);
                            
                            // Vérifier si c'est une agence
                            $isAgency = ($agencyCode || $agencyName) && 
                                       !isset($value['agencies']) && 
                                       !isset($value['totals']) && 
                                       !isset($value['service_points']);
                            
                            if ($isAgency && ($agencyCode || $agencyName)) {
                                // Chercher l'objectif cumulé (EPARGNE_SIMPLE + EPARGNE_PROJET)
                                $objectiveTotal = null;
                                
                                // 1. Recherche exacte par code
                                if ($agencyCode && isset($objectivesByCode[$agencyCode])) {
                                    $objectiveTotal = $objectivesByCode[$agencyCode];
                                }
                                // 2. Recherche exacte par nom
                                elseif ($agencyName && isset($objectivesByName[$agencyName])) {
                                    $objectiveTotal = $objectivesByName[$agencyName];
                                }
                                // 3. Recherche normalisée par code
                                elseif ($normalizedAgencyCode && isset($objectivesByNormalizedCode[$normalizedAgencyCode])) {
                                    $objectiveTotal = $objectivesByNormalizedCode[$normalizedAgencyCode];
                                }
                                // 4. Recherche normalisée par nom
                                elseif ($normalizedAgencyName && isset($objectivesByNormalizedName[$normalizedAgencyName])) {
                                    $objectiveTotal = $objectivesByNormalizedName[$normalizedAgencyName];
                                }
                                
                                if ($objectiveTotal !== null) {
                                    // Fusionner l'objectif cumulé
                                    $oldValue = $value['objectif'] ?? $value['OBJECTIF'] ?? 0;
                                    $value['OBJECTIF'] = (int)$objectiveTotal;
                                    $value['objectif'] = (int)$objectiveTotal;
                                    $mergedCount++;
                                    
                                    if ($mergedCount <= 5) {
                                        Log::info('✅ Objectif EPARGNE fusionné', [
                                            'agency_code' => $agencyCode,
                                            'agency_name' => $agencyName,
                                            'old_value' => $oldValue,
                                            'new_value' => $objectiveTotal
                                        ]);
                                    }
                                }
                            }
                            
                            // Récursion pour les structures imbriquées
                            if (isset($value['agencies']) && is_array($value['agencies'])) {
                                foreach ($value['agencies'] as &$agency) {
                                    $mergeRecursive($agency, $depth + 1);
                                }
                            }
                            
                            if (isset($value['service_points']) && is_array($value['service_points'])) {
                                if (isset($value['service_points']['agencies']) && is_array($value['service_points']['agencies'])) {
                                    foreach ($value['service_points']['agencies'] as &$agency) {
                                        $mergeRecursive($agency, $depth + 1);
                                    }
                                }
                            }
                            
                            $mergeRecursive($value, $depth + 1);
                        }
                    }
                }
            };
            
            // Fusionner dans hierarchicalData
            $dataToMerge = $data;
            if (isset($data['data']) && is_array($data['data'])) {
                $dataToMerge = $data['data'];
            }
            
            if (isset($dataToMerge['hierarchicalData'])) {
                // Parcourir TERRITOIRE
                if (isset($dataToMerge['hierarchicalData']['TERRITOIRE'])) {
                    foreach ($dataToMerge['hierarchicalData']['TERRITOIRE'] as $territoryKey => &$territory) {
                        if (isset($territory['agencies']) && is_array($territory['agencies'])) {
                            foreach ($territory['agencies'] as &$agency) {
                                $mergeRecursive($agency, 1);
                            }
                        }
                        $mergeRecursive($territory, 1);
                    }
                }
                
                // Parcourir POINT SERVICES
                if (isset($dataToMerge['hierarchicalData']['POINT SERVICES'])) {
                    foreach ($dataToMerge['hierarchicalData']['POINT SERVICES'] as $serviceKey => &$servicePoint) {
                        if (isset($servicePoint['service_points']['agencies']) && is_array($servicePoint['service_points']['agencies'])) {
                            foreach ($servicePoint['service_points']['agencies'] as &$agency) {
                                $mergeRecursive($agency, 1);
                            }
                        }
                        if (isset($servicePoint['agencies']) && is_array($servicePoint['agencies'])) {
                            foreach ($servicePoint['agencies'] as &$agency) {
                                $mergeRecursive($agency, 1);
                            }
                        }
                        $mergeRecursive($servicePoint, 1);
                    }
                }
                
                $mergeRecursive($dataToMerge['hierarchicalData'], 0);
            }
            
            // Si pas de hierarchicalData, récursion générale
            if (!isset($dataToMerge['hierarchicalData'])) {
                $mergeRecursive($dataToMerge, 0);
            }
            
            // Remettre les données fusionnées dans la structure originale
            if (isset($data['data']) && is_array($data['data'])) {
                $data['data'] = $dataToMerge;
            }
            
            Log::info('✅ Fusion EPARGNE terminée', [
                'objectifs_fusionnes' => $mergedCount,
                'objectifs_totaux' => $objectives->count()
            ]);
            
        } catch (\Exception $e) {
            Log::error('Erreur lors de la fusion des objectifs EPARGNE', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
        }
        
        return $data;
    }

    /**
     * Fusionne les objectifs personnalisés avec les données Oracle
     */
    private function mergeObjectivesWithData($data, $type, $year, $month = null)
    {
        try {
            // Récupérer tous les objectifs pour cette période depuis la base de données Laravel
            $objectivesQuery = Objective::where('type', $type)
                ->where('year', $year);
            
            if ($month) {
                $objectivesQuery->where(function($q) use ($month) {
                    $q->where(function($q2) use ($month) {
                        $q2->where('period', 'month')->where('month', $month);
                    })
                    ->orWhere('period', 'quarter')
                    ->orWhere('period', 'year');
                });
            } else {
                // Si pas de mois, prendre tous les objectifs de l'année
                $objectivesQuery->where(function($q) {
                    $q->where('period', 'year')
                      ->orWhere('period', 'quarter');
                });
            }
            
            $objectives = $objectivesQuery->get();
            
            Log::info('Objectifs trouvés pour fusion', [
                'count' => $objectives->count(),
                'type' => $type,
                'year' => $year,
                'month' => $month,
                'objectives' => $objectives->map(function($obj) {
                    return [
                        'id' => $obj->id,
                        'agency_code' => $obj->agency_code,
                        'agency_name' => $obj->agency_name,
                        'value' => $obj->value,
                        'category' => $obj->category
                    ];
                })->toArray()
            ]);
            
            // Créer un index pour recherche rapide par code et nom d'agence
            $objectivesByCode = [];
            $objectivesByName = [];
            foreach ($objectives as $objective) {
                $code = strtoupper(trim($objective->agency_code ?? ''));
                $name = strtoupper(trim($objective->agency_name ?? ''));
                if ($code) {
                    $objectivesByCode[$code] = $objective;
                }
                if ($name) {
                    $objectivesByName[$name] = $objective;
                }
            }
            
            Log::info('Index des objectifs créé', [
                'byCode' => count($objectivesByCode),
                'byName' => count($objectivesByName)
            ]);
            
            $mergedCount = 0;
            
            // Fonction pour normaliser les noms d'agences (supprimer accents, espaces multiples, etc.)
            $normalizeAgencyName = function($name) {
                $name = strtoupper(trim($name ?? ''));
                // Supprimer les accents
                $name = iconv('UTF-8', 'ASCII//TRANSLIT//IGNORE', $name);
                // Remplacer les espaces multiples par un seul
                $name = preg_replace('/\s+/', ' ', $name);
                return trim($name);
            };
            
            // Créer aussi un index normalisé
            $objectivesByNormalizedCode = [];
            $objectivesByNormalizedName = [];
            foreach ($objectives as $objective) {
                $code = $normalizeAgencyName($objective->agency_code);
                $name = $normalizeAgencyName($objective->agency_name);
                if ($code) {
                    $objectivesByNormalizedCode[$code] = $objective;
                }
                if ($name) {
                    $objectivesByNormalizedName[$name] = $objective;
                }
            }
            
            // Fonction récursive pour fusionner les objectifs dans la structure hiérarchique
            $mergeRecursive = function(&$item, $depth = 0) use (&$mergeRecursive, &$mergedCount, $normalizeAgencyName, $objectivesByCode, $objectivesByName, $objectivesByNormalizedCode, $objectivesByNormalizedName, $type) {
                if (is_array($item)) {
                    foreach ($item as $key => &$value) {
                        if (is_array($value)) {
                            // Extraire tous les champs possibles pour le nom/code d'agence
                            $possibleNames = [
                                $value['name'] ?? null,
                                $value['AGENCE'] ?? null,
                                $value['NOM_AGENCE'] ?? null,
                                $value['NOM'] ?? null,
                                $value['LIBELLE'] ?? null,
                                $value['LIBELLE_AGENCE'] ?? null
                            ];
                            
                            $possibleCodes = [
                                $value['code'] ?? null,
                                $value['CODE_AGENCE'] ?? null,
                                $value['CODE'] ?? null,
                                $value['AGENCE'] ?? null // AGENCE peut être code ou nom
                            ];
                            
                            // Prendre le premier non vide
                            $agencyName = '';
                            foreach ($possibleNames as $name) {
                                if (!empty($name)) {
                                    $agencyName = strtoupper(trim($name));
                                    break;
                                }
                            }
                            
                            $agencyCode = '';
                            foreach ($possibleCodes as $code) {
                                if (!empty($code)) {
                                    $agencyCode = strtoupper(trim($code));
                                    break;
                                }
                            }
                            
                            // Si pas de code, utiliser le nom comme code
                            if (empty($agencyCode) && !empty($agencyName)) {
                                $agencyCode = $agencyName;
                            }
                            
                            // Normaliser aussi pour la recherche
                            $normalizedAgencyName = $normalizeAgencyName($agencyName);
                            $normalizedAgencyCode = $normalizeAgencyName($agencyCode);
                            
                            // Vérifier si c'est une agence (a un nom ou code)
                            $isAgency = ($agencyCode || $agencyName) && 
                                       !isset($value['agencies']) && // Pas un conteneur d'agences
                                       !isset($value['totals']) && // Pas un total
                                       !isset($value['service_points']); // Pas un point de service
                            
                            if ($isAgency && ($agencyCode || $agencyName)) {
                                // Log pour déboguer (seulement les premières agences)
                                if ($mergedCount < 5 && $depth < 3) {
                                    Log::debug('🔍 Recherche objectif pour agence', [
                                        'agency_code' => $agencyCode,
                                        'agency_name' => $agencyName,
                                        'normalized_code' => $normalizedAgencyCode,
                                        'normalized_name' => $normalizedAgencyName,
                                        'value_keys' => array_keys($value),
                                        'depth' => $depth
                                    ]);
                                }
                                // Chercher un objectif correspondant (plusieurs stratégies)
                                $objective = null;
                                
                                // 1. Recherche exacte par code
                                if ($agencyCode && isset($objectivesByCode[$agencyCode])) {
                                    $objective = $objectivesByCode[$agencyCode];
                                }
                                // 2. Recherche exacte par nom
                                elseif ($agencyName && isset($objectivesByName[$agencyName])) {
                                    $objective = $objectivesByName[$agencyName];
                                }
                                // 3. Recherche normalisée par code
                                elseif ($normalizedAgencyCode && isset($objectivesByNormalizedCode[$normalizedAgencyCode])) {
                                    $objective = $objectivesByNormalizedCode[$normalizedAgencyCode];
                                }
                                // 4. Recherche normalisée par nom
                                elseif ($normalizedAgencyName && isset($objectivesByNormalizedName[$normalizedAgencyName])) {
                                    $objective = $objectivesByNormalizedName[$normalizedAgencyName];
                                }
                                // 5. Recherche croisée (code comme nom)
                                elseif ($agencyCode && isset($objectivesByName[$agencyCode])) {
                                    $objective = $objectivesByName[$agencyCode];
                                }
                                // 6. Recherche croisée (nom comme code)
                                elseif ($agencyName && isset($objectivesByCode[$agencyName])) {
                                    $objective = $objectivesByCode[$agencyName];
                                }
                                // 7. Recherche partielle (contient) - plus flexible
                                else {
                                    // Recherche dans les codes normalisés
                                    foreach ($objectivesByNormalizedCode as $objCode => $obj) {
                                        if (!empty($normalizedAgencyCode) && !empty($objCode)) {
                                            // Vérifier si l'un contient l'autre (au moins 3 caractères communs)
                                            if (strlen($normalizedAgencyCode) >= 3 && strlen($objCode) >= 3) {
                                                if (stripos($normalizedAgencyCode, $objCode) !== false || 
                                                    stripos($objCode, $normalizedAgencyCode) !== false) {
                                                    $objective = $obj;
                                                    Log::info('Match partiel trouvé (code)', [
                                                        'agency_code' => $normalizedAgencyCode,
                                                        'objective_code' => $objCode
                                                    ]);
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                    // Recherche dans les noms normalisés
                                    if (!$objective) {
                                        foreach ($objectivesByNormalizedName as $objName => $obj) {
                                            if (!empty($normalizedAgencyName) && !empty($objName)) {
                                                if (strlen($normalizedAgencyName) >= 3 && strlen($objName) >= 3) {
                                                    if (stripos($normalizedAgencyName, $objName) !== false || 
                                                        stripos($objName, $normalizedAgencyName) !== false) {
                                                        $objective = $obj;
                                                        Log::info('Match partiel trouvé (nom)', [
                                                            'agency_name' => $normalizedAgencyName,
                                                            'objective_name' => $objName
                                                        ]);
                                                        break;
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                                
                                if ($objective) {
                                    // Fusionner l'objectif (priorité aux objectifs personnalisés)
                                    $oldValue = $value['objectif'] ?? $value['OBJECTIF_CLIENT'] ?? $value['OBJECTIF_PRODUCTION'] ?? $value['OBJECTIF_COFICARTE'] ?? 0;
                                    if ($type === 'CLIENT') {
                                        $value['OBJECTIF_CLIENT'] = (int)$objective->value;
                                        $value['objectif'] = (int)$objective->value;
                                    } elseif ($type === 'PREPAID_CARD') {
                                        $value['OBJECTIF_COFICARTE'] = (int)$objective->value;
                                        $value['objectif'] = (int)$objective->value;
                                        // Recalculer le taux de réalisation si nécessaire
                                        $nombreM = $value['NOMBRE_COFICARTE_VENDU_M'] ?? 0;
                                        if ($nombreM > 0 && (int)$objective->value > 0) {
                                            $value['TAUX_REALISATION'] = round(($nombreM / (int)$objective->value) * 100, 2);
                                        }
                                    } else {
                                        $value['OBJECTIF_PRODUCTION'] = (int)$objective->value;
                                        $value['objectif'] = (int)$objective->value;
                                    }
                                    $mergedCount++;
                                    Log::info('✅ Objectif fusionné avec succès', [
                                        'agency_code_oracle' => $agencyCode,
                                        'agency_name_oracle' => $agencyName,
                                        'objective_code' => strtoupper(trim($objective->agency_code ?? '')),
                                        'objective_name' => strtoupper(trim($objective->agency_name ?? '')),
                                        'old_value' => $oldValue,
                                        'new_value' => $objective->value,
                                        'objective_id' => $objective->id,
                                        'depth' => $depth
                                    ]);
                                } else {
                                    // Log pour déboguer les non-matchs (seulement pour les premières agences)
                                    if ($depth < 2 && count($objectivesByCode) > 0 && ($agencyCode || $agencyName)) {
                                        Log::debug('⚠️ Aucun objectif trouvé pour agence', [
                                            'agency_code_oracle' => $agencyCode,
                                            'agency_name_oracle' => $agencyName,
                                            'normalized_code' => $normalizedAgencyCode,
                                            'normalized_name' => $normalizedAgencyName,
                                            'available_objective_codes' => array_slice(array_keys($objectivesByCode), 0, 10),
                                            'available_objective_names' => array_slice(array_keys($objectivesByName), 0, 10),
                                            'value_keys' => array_keys($value),
                                            'value_sample' => [
                                                'name' => $value['name'] ?? null,
                                                'AGENCE' => $value['AGENCE'] ?? null,
                                                'CODE_AGENCE' => $value['CODE_AGENCE'] ?? null,
                                                'NOM_AGENCE' => $value['NOM_AGENCE'] ?? null
                                            ]
                                        ]);
                                    }
                                }
                            }
                            
                            // Récursion pour les structures imbriquées (agencies, service_points, etc.)
                            if (isset($value['agencies']) && is_array($value['agencies'])) {
                                foreach ($value['agencies'] as &$agency) {
                                    $mergeRecursive($agency, $depth + 1);
                                }
                            }
                            
                            // Récursion pour service_points.agencies (structure POINT SERVICES)
                            if (isset($value['service_points']) && is_array($value['service_points'])) {
                                if (isset($value['service_points']['agencies']) && is_array($value['service_points']['agencies'])) {
                                    foreach ($value['service_points']['agencies'] as &$agency) {
                                        $mergeRecursive($agency, $depth + 1);
                                    }
                                }
                            }
                            
                            // Récursion générale
                            $mergeRecursive($value, $depth + 1);
                        }
                    }
                }
            };
            
            // Vérifier d'abord si les données sont dans une clé 'data'
            $dataToMerge = $data;
            if (isset($data['data']) && is_array($data['data'])) {
                $dataToMerge = $data['data'];
                Log::info('📦 Données trouvées dans data.data, utilisation de cette structure');
            }
            
            // Fusionner dans hierarchicalData (structure principale)
            if (isset($dataToMerge['hierarchicalData'])) {
                Log::info('🔍 Fusion dans hierarchicalData', [
                    'has_hierarchicalData' => true,
                    'keys' => array_keys($dataToMerge['hierarchicalData'] ?? [])
                ]);
                
                // Parcourir spécifiquement TERRITOIRE et ses agences
                if (isset($dataToMerge['hierarchicalData']['TERRITOIRE'])) {
                    foreach ($dataToMerge['hierarchicalData']['TERRITOIRE'] as $territoryKey => &$territory) {
                        if (isset($territory['agencies']) && is_array($territory['agencies'])) {
                            Log::info('Parcours des agences du territoire', [
                                'territory' => $territoryKey,
                                'agencies_count' => count($territory['agencies'])
                            ]);
                            foreach ($territory['agencies'] as &$agency) {
                                $mergeRecursive($agency, 1);
                            }
                        }
                        // Aussi parcourir récursivement pour les autres structures
                        $mergeRecursive($territory, 1);
                    }
                }
                
                // Parcourir POINT SERVICES
                if (isset($dataToMerge['hierarchicalData']['POINT SERVICES'])) {
                    foreach ($dataToMerge['hierarchicalData']['POINT SERVICES'] as $serviceKey => &$servicePoint) {
                        if (isset($servicePoint['service_points']['agencies']) && is_array($servicePoint['service_points']['agencies'])) {
                            foreach ($servicePoint['service_points']['agencies'] as &$agency) {
                                $mergeRecursive($agency, 1);
                            }
                        }
                        if (isset($servicePoint['agencies']) && is_array($servicePoint['agencies'])) {
                            foreach ($servicePoint['agencies'] as &$agency) {
                                $mergeRecursive($agency, 1);
                            }
                        }
                        $mergeRecursive($servicePoint, 1);
                    }
                }
                
                // Récursion générale pour le reste
                $mergeRecursive($dataToMerge['hierarchicalData'], 0);
            }
            
            // Si pas de hierarchicalData, essayer une récursion générale
            if (!isset($dataToMerge['hierarchicalData'])) {
                Log::info('⚠️ Pas de hierarchicalData, récursion générale sur toute la structure');
                $mergeRecursive($dataToMerge, 0);
            }
            
            // Fusionner dans territories (structure alternative)
            if (isset($dataToMerge['territories'])) {
                Log::info('🔍 Fusion dans territories', [
                    'has_territories' => true,
                    'keys' => array_keys($dataToMerge['territories'] ?? [])
                ]);
                $mergeRecursive($dataToMerge['territories']);
            }
            
            // Fusionner dans les agences directement
            if (isset($dataToMerge['agencies'])) {
                Log::info('🔍 Fusion dans agencies', [
                    'has_agencies' => true,
                    'count' => count($dataToMerge['agencies'] ?? [])
                ]);
                $mergeRecursive($dataToMerge['agencies']);
            }
            
            // Remettre les données fusionnées dans la structure originale si nécessaire
            if (isset($data['data']) && is_array($data['data'])) {
                $data['data'] = $dataToMerge;
            }
            
            Log::info('✅ Fusion terminée', [
                'objectifs_fusionnes' => $mergedCount,
                'objectifs_totaux' => $objectives->count(),
                'structure_keys' => array_keys($data ?? []),
                'has_hierarchicalData' => isset($dataToMerge['hierarchicalData']),
                'has_territories' => isset($dataToMerge['territories'])
            ]);
            
        } catch (\Exception $e) {
            Log::error('Erreur lors de la fusion des objectifs', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
        }
        
        return $data;
    }

    /**
     * Récupère les données de production depuis Oracle via l'API Python
     */
    public function getProductionData(Request $request): JsonResponse
    {
        try {
            // Construire l'URL de l'API Python
            $apiUrl = $this->pythonServiceUrl . '/api/oracle/data/production';
            
            // Récupérer les paramètres de la requête
            $month = $request->input('month');
            $year = $request->input('year');
            $dateM_debut = $request->input('date_m_debut');
            $dateM_fin = $request->input('date_m_fin');
            
            // Construire les paramètres de requête
            $params = [];
            if ($month && $year) {
                // Mois spécifique
                $params['month'] = $month;
                $params['year'] = $year;
            } elseif ($year && !$month) {
                // Année complète (sans mois)
                $params['year'] = $year;
            } elseif ($dateM_debut && $dateM_fin) {
                // Dates personnalisées
                $params['date_m_debut'] = $dateM_debut;
                $params['date_m_fin'] = $dateM_fin;
            } else {
                // Utiliser le mois et l'année actuels par défaut
                $params['month'] = (int)date('n');
                $params['year'] = (int)date('Y');
            }
            
            // Faire l'appel à l'API Python
            $response = Http::timeout(30)->get($apiUrl, $params);
            
            if ($response->successful()) {
                return response()->json($response->json());
            }
            
            // En cas d'erreur, retourner le message d'erreur
            $errorData = $response->json();
            Log::error('Erreur API Python Production', [
                'status' => $response->status(),
                'error' => $errorData
            ]);
            
            return response()->json([
                'error' => 'Erreur lors de la récupération des données',
                'detail' => $errorData['detail'] ?? $response->body(),
                'status' => $response->status()
            ], $response->status() ?: 500);
            
        } catch (\Exception $e) {
            Log::error('Exception lors de l\'appel API Python Production', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return response()->json([
                'error' => 'Erreur de connexion au service Python',
                'detail' => $e->getMessage()
            ], 500);
        }
    }
    
    /**
     * Récupère les données de production en volume depuis Oracle via l'API Python
     */
    public function getProductionVolumeData(Request $request): JsonResponse
    {
        try {
            // Construire l'URL de l'API Python
            $apiUrl = $this->pythonServiceUrl . '/api/oracle/data/production-volume';
            
            // Récupérer les paramètres de la requête
            $month = $request->input('month');
            $year = $request->input('year');
            $dateM_debut = $request->input('date_m_debut');
            $dateM_fin = $request->input('date_m_fin');
            
            // Construire les paramètres de requête
            $params = [];
            if ($month && $year) {
                // Mois spécifique
                $params['month'] = $month;
                $params['year'] = $year;
            } elseif ($year && !$month) {
                // Année complète (sans mois)
                $params['year'] = $year;
            } elseif ($dateM_debut && $dateM_fin) {
                // Dates personnalisées
                $params['date_m_debut'] = $dateM_debut;
                $params['date_m_fin'] = $dateM_fin;
            } else {
                // Utiliser le mois et l'année actuels par défaut
                $params['month'] = (int)date('n');
                $params['year'] = (int)date('Y');
            }
            
            // Faire l'appel à l'API Python
            $response = Http::timeout(30)->get($apiUrl, $params);
            
            if ($response->successful()) {
                return response()->json($response->json());
            }
            
            // En cas d'erreur, retourner le message d'erreur
            $errorData = $response->json();
            Log::error('Erreur API Python Production Volume', [
                'status' => $response->status(),
                'error' => $errorData
            ]);
            
            return response()->json([
                'error' => 'Erreur lors de la récupération des données',
                'detail' => $errorData['detail'] ?? $response->body(),
                'status' => $response->status()
            ], $response->status() ?: 500);
            
        } catch (\Exception $e) {
            Log::error('Exception lors de l\'appel API Python Production Volume', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return response()->json([
                'error' => 'Erreur de connexion au service Python',
                'detail' => $e->getMessage()
            ], 500);
        }
    }
    
    /**
     * Récupère les données d'encours épargne depuis Oracle
     */
    public function getEncoursData(Request $request): JsonResponse
    {
        try {
            $period = $request->input('period', 'month');
            $zone = $request->input('zone');
            $month = $request->input('month');
            $year = $request->input('year');
            $date = $request->input('date'); // Pour la période "week"
            $type = $request->input('type', 'epargne-pep-simple'); // Type de filtre

            // Appeler le service Oracle pour récupérer les données d'encours épargne
            $result = $this->oracleService->getEncoursEpargneData($period, $zone, $month ? (int)$month : null, $year ? (int)$year : null, $date, $type);

            if ($result['success']) {
                $data = $result['data'];
                
                // Les données peuvent être dans $data directement ou dans $data['data']
                $actualData = $data;
                if (isset($data['data']) && is_array($data['data'])) {
                    $actualData = $data['data'];
                }
                
                // Fusionner les objectifs EPARGNE_SIMPLE et EPARGNE_PROJET (cumul des deux)
                // Utiliser l'année et le mois de la requête, ou les valeurs actuelles
                $mergeYear = $year ? (int)$year : (int)date('Y');
                $mergeMonth = null;
                
                // Déterminer le mois selon la période
                if ($period === 'month' && $month) {
                    $mergeMonth = (int)$month;
                } elseif ($period === 'week' && $date) {
                    // Extraire le mois de la date
                    $dateObj = \DateTime::createFromFormat('Y-m-d', $date);
                    if ($dateObj) {
                        $mergeMonth = (int)$dateObj->format('n');
                    }
                } elseif ($period === 'month') {
                    $mergeMonth = (int)date('n');
                }
                
                Log::info('🔄 Début fusion des objectifs EPARGNE', [
                    'year' => $mergeYear,
                    'month' => $mergeMonth,
                    'period' => $period
                ]);
                
                // Fusionner EPARGNE_SIMPLE et EPARGNE_PROJET et les additionner
                $actualData = $this->mergeEpargneObjectivesWithData($actualData, $mergeYear, $mergeMonth);
                
                // Remettre les données fusionnées dans la structure originale
                if (isset($data['data'])) {
                    $data['data'] = $actualData;
                } else {
                    $data = $actualData;
                }
                
                Log::info('✅ Données EPARGNE fusionnées retournées au client');
                
                return response()->json($data);
            }

            Log::error('Erreur lors de la récupération des données encours épargne', [
                'error' => $result['error'],
                'message' => $result['message']
            ]);

            return response()->json([
                'error' => $result['error'],
                'message' => $result['message']
            ], 500);
        } catch (\Exception $e) {
            Log::error('Exception lors de la récupération des données encours épargne', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);

            return response()->json([
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Récupère les données de collecte depuis Oracle
     */
    public function getCollectionData(Request $request): JsonResponse
    {
        try {
            $period = $request->input('period', 'month');
            $zone = $request->input('zone');
            $month = $request->input('month');
            $year = $request->input('year');
            $date = $request->input('date'); // Pour la période "week"

            // Appeler le service Oracle pour récupérer les données de collecte
            $result = $this->oracleService->getCollectionData($period, $zone, $month ? (int)$month : null, $year ? (int)$year : null, $date);

            if ($result['success']) {
                $data = $result['data'];
                
                // Les données peuvent être dans $data directement ou dans $data['data']
                $actualData = $data;
                if (isset($data['data']) && is_array($data['data'])) {
                    $actualData = $data['data'];
                }
                
                // Remettre les données dans la structure originale
                if (isset($data['data'])) {
                    $data['data'] = $actualData;
                } else {
                    $data = $actualData;
                }
                
                return response()->json($data);
            }

            Log::error('Erreur lors de la récupération des données collecte', [
                'error' => $result['error'],
                'message' => $result['message']
            ]);

            return response()->json([
                'error' => $result['error'],
                'message' => $result['message']
            ], 500);
        } catch (\Exception $e) {
            Log::error('Exception lors de la récupération des données collecte', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);

            return response()->json([
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Récupère les données de volume DAT depuis Oracle
     */
    public function getVolumeDatData(Request $request): JsonResponse
    {
        try {
            $period = $request->input('period', 'month');
            $zone = $request->input('zone');
            $month = $request->input('month');
            $year = $request->input('year');
            $date = $request->input('date'); // Pour la période "week"

            // Appeler le service Oracle pour récupérer les données de volume DAT
            $result = $this->oracleService->getVolumeDatData($period, $zone, $month ? (int)$month : null, $year ? (int)$year : null, $date);

            if ($result['success']) {
                $data = $result['data'];
                
                // Les données peuvent être dans $data directement ou dans $data['data']
                $actualData = $data;
                if (isset($data['data']) && is_array($data['data'])) {
                    $actualData = $data['data'];
                }
                
                // Remettre les données dans la structure originale
                if (isset($data['data'])) {
                    $data['data'] = $actualData;
                } else {
                    $data = $actualData;
                }
                
                return response()->json($data);
            }

            Log::error('Erreur lors de la récupération des données volume DAT', [
                'error' => $result['error'],
                'message' => $result['message']
            ]);

            return response()->json([
                'error' => $result['error'],
                'message' => $result['message']
            ], 500);
        } catch (\Exception $e) {
            Log::error('Exception lors de la récupération des données volume DAT', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);

            return response()->json([
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Récupère les données de dépôt de garantie depuis Oracle
     */
    public function getDepotGarantieData(Request $request): JsonResponse
    {
        try {
            $period = $request->input('period', 'month');
            $zone = $request->input('zone');
            $month = $request->input('month');
            $year = $request->input('year');
            $date = $request->input('date'); // Pour la période "week"

            // Appeler le service Oracle pour récupérer les données de dépôt de garantie
            $result = $this->oracleService->getDepotGarantieData($period, $zone, $month ? (int)$month : null, $year ? (int)$year : null, $date);

            if ($result['success']) {
                $data = $result['data'];
                
                // Les données peuvent être dans $data directement ou dans $data['data']
                $actualData = $data;
                if (isset($data['data']) && is_array($data['data'])) {
                    $actualData = $data['data'];
                }
                
                // Remettre les données dans la structure originale
                if (isset($data['data'])) {
                    $data['data'] = $actualData;
                } else {
                    $data = $actualData;
                }
                
                return response()->json($data);
            }

            Log::error('Erreur lors de la récupération des données dépôt de garantie', [
                'error' => $result['error'],
                'message' => $result['message']
            ]);

            return response()->json([
                'error' => $result['error'],
                'message' => $result['message']
            ], 500);
        } catch (\Exception $e) {
            Log::error('Exception lors de la récupération des données dépôt de garantie', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);

            return response()->json([
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Récupère les données de ventes de cartes prépayées depuis Oracle via l'API Python
     */
    public function getPrepaidCardSalesData(Request $request): JsonResponse
    {
        try {
            $period = $request->input('period', 'month');
            $zone = $request->input('zone');
            $month = $request->input('month');
            $year = $request->input('year');
            $date = $request->input('date'); // Pour la période "week"

            // Construire l'URL de l'API Python
            $apiUrl = $this->pythonServiceUrl . '/api/oracle/data/prepaid-card-sales';
            
            // Construire les paramètres de requête
            $params = [];
            if ($period) {
                $params['period'] = $period;
            }
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
            
            // Faire l'appel à l'API Python
            $response = Http::timeout(300)->get($apiUrl, $params);
            
            if ($response->successful()) {
                $data = $response->json();
                
                // Les données peuvent être dans $data directement ou dans $data['data']
                $actualData = $data;
                if (isset($data['data']) && is_array($data['data'])) {
                    $actualData = $data['data'];
                }
                
                // Fusionner les objectifs personnalisés avec les données Oracle
                // Utiliser l'année et le mois de la requête, ou les valeurs actuelles
                $mergeYear = $year ? (int)$year : (int)date('Y');
                $mergeMonth = null;
                
                // Déterminer le mois selon la période
                if ($period === 'month' && $month) {
                    $mergeMonth = (int)$month;
                } elseif ($period === 'week' && $date) {
                    // Extraire le mois de la date
                    $dateObj = \DateTime::createFromFormat('Y-m-d', $date);
                    if ($dateObj) {
                        $mergeMonth = (int)$dateObj->format('n');
                    }
                } elseif ($period === 'month') {
                    $mergeMonth = (int)date('n');
                }
                
                Log::info('🔄 Début fusion des objectifs PREPAID_CARD', [
                    'year' => $mergeYear,
                    'month' => $mergeMonth,
                    'period' => $period
                ]);
                
                // Fusionner les objectifs (utiliser 'PREPAID_CARD' comme type)
                $actualData = $this->mergeObjectivesWithData($actualData, 'PREPAID_CARD', $mergeYear, $mergeMonth);
                
                // Remettre les données fusionnées dans la structure originale
                if (isset($data['data'])) {
                    $data['data'] = $actualData;
                } else {
                    $data = $actualData;
                }
                
                Log::info('✅ Données PREPAID_CARD fusionnées retournées au client');
                
                return response()->json($data);
            }
            
            // En cas d'erreur, retourner le message d'erreur
            $errorData = $response->json();
            Log::error('Erreur API Python Ventes Cartes Prépayées', [
                'status' => $response->status(),
                'error' => $errorData
            ]);
            
            return response()->json([
                'error' => 'Erreur lors de la récupération des données',
                'detail' => $errorData['detail'] ?? $response->body(),
                'status' => $response->status()
            ], $response->status() ?: 500);
            
        } catch (\Exception $e) {
            Log::error('Exception lors de l\'appel API Python Ventes Cartes Prépayées', [
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ]);
            
            return response()->json([
                'error' => 'Erreur de connexion au service Python',
                'detail' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Récupère les données d'une table spécifique
     */
    public function getTableData(Request $request, string $tableName): JsonResponse
    {
        $limit = $request->input('limit', 100);
        $offset = $request->input('offset', 0);

        $result = $this->oracleService->table($tableName, $limit, $offset);

        if ($result['success']) {
            return response()->json($result['data']);
        }

        return response()->json([
            'error' => $result['error'],
            'message' => $result['message']
        ], 500);
    }
}

