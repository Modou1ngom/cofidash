<?php

namespace App\Http\Controllers;

use App\Services\OracleService;
use App\Models\Objective;
use App\Models\User;
use App\Models\Territory;
use App\Models\Agency;
use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Validator;

class ObjectiveController extends Controller
{
    protected $oracleService;

    public function __construct(OracleService $oracleService)
    {
        $this->oracleService = $oracleService;
    }

    /**
     * Récupère la liste des objectifs depuis la base de données Laravel
     */
    public function index(Request $request): JsonResponse
    {
        try {
            $type = $request->input('type');
            $category = $request->input('category');
            $year = $request->input('year');
            $month = $request->input('month');
            $agencyCode = $request->input('agency_code');

            $query = Objective::query();

            if ($type) {
                $query->where('type', $type);
            }
            if ($category) {
                $query->where('category', $category);
            }
            if ($year) {
                $query->where('year', $year);
            }
            if ($month) {
                $query->where(function($q) use ($month) {
                    $q->where('period', 'month')->where('month', $month)
                      ->orWhere('period', 'quarter')
                      ->orWhere('period', 'year');
                });
            }
            if ($agencyCode) {
                $query->where('agency_code', $agencyCode);
            }

            $objectives = $query->get();

            return response()->json([
                'success' => true,
                'data' => $objectives
            ]);
        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des objectifs: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Erreur lors de la récupération des objectifs'
            ], 500);
        }
    }

    /**
     * Détermine le statut initial selon le profil de l'utilisateur
     */
    private function getInitialStatus(User $user): string
    {
        $profileCode = $user->profile->code ?? null;
        
        switch ($profileCode) {
            case 'DGA':
                // DGA fixe pour les zones, doit être validé par MD
                return 'pending_validation';
            case 'RESPONSABLE_ZONE':
                // Responsable Zone fixe pour les agences, doit être validé par DGA
                return 'pending_validation';
            case 'CHEF_AGENCE':
                // Chef d'Agence fixe pour ses CAF, doit être validé par Responsable Zone
                return 'pending_validation';
            case 'MD':
            case 'ADMIN':
                // MD et Admin peuvent valider directement
                return 'validated';
            default:
                return 'draft';
        }
    }

    /**
     * Vérifie si l'utilisateur peut créer un objectif pour cette catégorie
     */
    private function canCreateObjective(User $user, string $category): bool
    {
        $profileCode = $user->profile->code ?? null;
        
        switch ($profileCode) {
            case 'DGA':
                // DGA répartit l'objectif MD (filiale) entre les territoires
                return $category === 'TERRITOIRE';
            case 'RESPONSABLE_ZONE':
                // Agences du territoire (anciennement « point de service ») + grands comptes
                return in_array($category, ['TERRITOIRE', 'POINT SERVICES', 'GRAND COMPTE']);
            case 'CHEF_AGENCE':
                return in_array($category, ['TERRITOIRE', 'POINT SERVICES', 'GRAND COMPTE']);
            case 'MD':
                // MD crée pour la filiale (objectif global annuel)
                return $category === 'FILIALE';
            case 'ADMIN':
                // Admin peut créer pour toutes les catégories
                return true;
            default:
                return false;
        }
    }

    /**
     * Crée un nouvel objectif
     */
    public function store(Request $request): JsonResponse
    {
        $rules = [
            'type' => 'required|in:CLIENT,PRODUCTION,ENCOURS_CREDIT,COLLECT,DEPOT_GARANTIE,EPARGNE_SIMPLE,EPARGNE_PROJET,VOLUME_DAT',
            'category' => 'required|in:FILIALE,TERRITOIRE,POINT SERVICES,GRAND COMPTE',
            'agency_code' => 'required|string',
            'value' => 'required|integer|min:0',
            'value_nombres' => 'nullable|integer|min:0',
            'value_volume' => 'nullable|integer|min:0',
            'period' => 'required|in:month,quarter,year',
            'year' => 'required|integer|min:2020|max:2100',
            'month' => 'nullable|integer|min:1|max:12',
            'quarter' => 'nullable|integer|min:1|max:4',
            'description' => 'nullable|string|max:500',
            'zone' => 'nullable|string',
            'territory' => 'nullable|string'
        ];

        // Pour PRODUCTION, value_nombres et value_volume sont requis
        if ($request->input('type') === 'PRODUCTION') {
            $rules['value_nombres'] = 'required|integer|min:0';
            $rules['value_volume'] = 'required|integer|min:0';
        }

        // Ajouter les règles conditionnelles pour month et quarter
        if ($request->input('period') === 'month') {
            $rules['month'] = 'required|integer|min:1|max:12';
        } elseif ($request->input('period') === 'quarter') {
            $rules['quarter'] = 'required|integer|min:1|max:4';
        }

        $validator = Validator::make($request->all(), $rules, [
            'type.required' => 'Le type d\'objectif est requis.',
            'type.in' => 'Le type d\'objectif doit être CLIENT, PRODUCTION, ENCOURS_CREDIT, COLLECT, DEPOT_GARANTIE, EPARGNE_SIMPLE, EPARGNE_PROJET ou VOLUME_DAT.',
            'category.required' => 'La catégorie est requise.',
            'category.in' => 'La catégorie doit être FILIALE, TERRITOIRE, POINT SERVICES (historique) ou GRAND COMPTE.',
            'agency_code.required' => 'Le code de l\'agence est requis.',
            'value.required' => 'La valeur de l\'objectif est requise.',
            'value.integer' => 'La valeur de l\'objectif doit être un nombre entier.',
            'value.min' => 'La valeur de l\'objectif doit être supérieure ou égale à 0.',
            'period.required' => 'La période est requise.',
            'period.in' => 'La période doit être month, quarter ou year.',
            'year.required' => 'L\'année est requise.',
            'year.integer' => 'L\'année doit être un nombre entier.',
            'year.min' => 'L\'année doit être supérieure ou égale à 2020.',
            'year.max' => 'L\'année doit être inférieure ou égale à 2100.',
            'month.required' => 'Le mois est requis pour une période mensuelle.',
            'month.integer' => 'Le mois doit être un nombre entier.',
            'month.min' => 'Le mois doit être entre 1 et 12.',
            'month.max' => 'Le mois doit être entre 1 et 12.',
            'quarter.required' => 'Le trimestre est requis pour une période trimestrielle.',
            'quarter.integer' => 'Le trimestre doit être un nombre entier.',
            'quarter.min' => 'Le trimestre doit être entre 1 et 4.',
            'quarter.max' => 'Le trimestre doit être entre 1 et 4.',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Données invalides',
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $user = Auth::user();
            if (!$user) {
                return response()->json([
                    'success' => false,
                    'message' => 'Utilisateur non authentifié'
                ], 401);
            }

            $data = $request->all();
            
            // Vérifier les permissions selon le profil
            if (!$this->canCreateObjective($user, $data['category'])) {
                return response()->json([
                    'success' => false,
                    'message' => 'Vous n\'avez pas la permission de créer un objectif pour cette catégorie'
                ], 403);
            }
            
            // Déterminer le statut initial
            $status = $this->getInitialStatus($user);
            
            // Vérifier si un objectif existe déjà pour cette agence, période, type
            $existingObjective = Objective::where('type', $data['type'])
                ->where('category', $data['category'])
                ->where('agency_code', $data['agency_code'])
                ->where('year', $data['year'])
                ->where(function($query) use ($data) {
                    if ($data['period'] === 'month' && $data['month']) {
                        $query->where('period', 'month')->where('month', $data['month']);
                    } elseif ($data['period'] === 'quarter' && $data['quarter']) {
                        $query->where('period', 'quarter')->where('quarter', $data['quarter']);
                    } elseif ($data['period'] === 'year') {
                        $query->where('period', 'year');
                    }
                })
                ->first();
            
            if ($existingObjective) {
                // Vérifier si l'utilisateur peut modifier cet objectif
                if ($existingObjective->status === 'validated' && $user->profile->code !== 'ADMIN' && $user->profile->code !== 'MD') {
                    return response()->json([
                        'success' => false,
                        'message' => 'Cet objectif est déjà validé et ne peut pas être modifié'
                    ], 403);
                }
                
                // Mettre à jour l'objectif existant
                $updateData = [
                    'value' => $data['value'],
                    'description' => $data['description'] ?? null,
                    'agency_name' => $data['agency_name'] ?? null,
                    'territory' => $data['territory'] ?? null,
                    'zone' => $data['zone'] ?? null,
                    'status' => $status,
                    'created_by' => $user->id
                ];

                // Ajouter value_nombres et value_volume si présents (pour PRODUCTION)
                if (isset($data['value_nombres'])) {
                    $updateData['value_nombres'] = $data['value_nombres'];
                }
                if (isset($data['value_volume'])) {
                    $updateData['value_volume'] = $data['value_volume'];
                }

                $existingObjective->update($updateData);
                
                return response()->json([
                    'success' => true,
                    'message' => $status === 'pending_validation' 
                        ? 'Objectif mis à jour et en attente de validation' 
                        : 'Objectif mis à jour avec succès',
                    'data' => $existingObjective
                ], 200);
            }
            
            // Créer un nouvel objectif dans la base de données Laravel
            $objectiveData = [
                'type' => $data['type'],
                'category' => $data['category'],
                'territory' => $data['territory'] ?? null,
                'zone' => $data['zone'] ?? null,
                'agency_code' => $data['agency_code'],
                'agency_name' => $data['agency_name'] ?? null,
                'value' => $data['value'],
                'period' => $data['period'],
                'year' => $data['year'],
                'month' => $data['month'] ?? null,
                'quarter' => $data['quarter'] ?? null,
                'description' => $data['description'] ?? null,
                'status' => $status,
                'created_by' => $user->id
            ];

            // Ajouter value_nombres et value_volume si présents (pour PRODUCTION)
            if (isset($data['value_nombres'])) {
                $objectiveData['value_nombres'] = $data['value_nombres'];
            }
            if (isset($data['value_volume'])) {
                $objectiveData['value_volume'] = $data['value_volume'];
            }

            $objective = Objective::create($objectiveData);

            Log::info('Objectif créé avec succès', [
                'id' => $objective->id,
                'status' => $status,
                'user' => $user->id,
                'profile' => $user->profile->code ?? 'N/A'
            ]);

            return response()->json([
                'success' => true,
                'message' => $status === 'pending_validation' 
                    ? 'Objectif créé et en attente de validation' 
                    : 'Objectif créé avec succès',
                'data' => $objective
            ], 201);

        } catch (\Exception $e) {
            Log::error('Erreur lors de la création de l\'objectif: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Erreur lors de la création de l\'objectif: ' . $e->getMessage()
            ], 500);
        }
    }

    /**
     * Met à jour un objectif existant dans la base de données Laravel
     */
    public function update(Request $request, $id): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'value' => 'sometimes|required|numeric|min:0',
            'description' => 'nullable|string|max:500'
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Données invalides',
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $objective = Objective::find($id);
            
            if (!$objective) {
                return response()->json([
                    'success' => false,
                    'message' => 'Objectif non trouvé'
                ], 404);
            }
            
            $objective->update($request->only(['value', 'description']));
            
            Log::info('Objectif mis à jour avec succès', ['id' => $id]);

            return response()->json([
                'success' => true,
                'message' => 'Objectif mis à jour avec succès',
                'data' => $objective
            ]);

        } catch (\Exception $e) {
            Log::error('Erreur lors de la mise à jour de l\'objectif: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Erreur lors de la mise à jour de l\'objectif'
            ], 500);
        }
    }

    /**
     * Récupère l'objectif DGA pour un territoire donné
     * Utilisé par les Responsables Zone pour pré-remplir le formulaire
     */
    /**
     * Récupère l'objectif MD (filiale) pour le DGA
     */
    public function getMDFilialeObjective(Request $request): JsonResponse
    {
        try {
            $validator = Validator::make($request->all(), [
                'type' => 'required|in:CLIENT,PRODUCTION,ENCOURS_CREDIT,COLLECT,DEPOT_GARANTIE,EPARGNE_SIMPLE,EPARGNE_PROJET,VOLUME_DAT',
                'period' => 'required|in:month,quarter,year',
                'year' => 'required|integer|min:2020|max:2100',
                'month' => 'nullable|integer|min:1|max:12',
                'quarter' => 'nullable|integer|min:1|max:4',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Données invalides',
                    'errors' => $validator->errors()
                ], 422);
            }

            $data = $validator->validated();

            // Récupérer l'objectif MD (filiale) validé pour l'année
            $objective = Objective::where('category', 'FILIALE')
                ->where('type', $data['type'])
                ->where('year', $data['year'])
                ->where(function($query) use ($data) {
                    if ($data['period'] === 'month' && $data['month']) {
                        $query->where('period', 'month')->where('month', $data['month']);
                    } elseif ($data['period'] === 'quarter' && $data['quarter']) {
                        $query->where('period', 'quarter')->where('quarter', $data['quarter']);
                    } elseif ($data['period'] === 'year') {
                        $query->where('period', 'year');
                    }
                })
                ->whereHas('creator', function($q) {
                    $q->whereHas('profile', function($q2) {
                        $q2->where('code', 'MD');
                    });
                })
                ->where('status', 'validated')
                ->orderBy('created_at', 'desc')
                ->first();

            if ($objective) {
                return response()->json([
                    'success' => true,
                    'data' => [
                        'value' => $objective->value,
                        'description' => $objective->description,
                        'objective_id' => $objective->id
                    ]
                ]);
            }

            return response()->json([
                'success' => false,
                'message' => 'Aucun objectif MD (filiale) validé trouvé pour cette période'
            ], 404);

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération de l\'objectif MD (filiale): ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Erreur interne lors de la récupération de l\'objectif MD (filiale).'
            ], 500);
        }
    }

    /**
     * Récupère l'objectif DGA (territoire) pour le Responsable Zone
     */
    public function getDGAObjective(Request $request): JsonResponse
    {
        try {
            $validator = Validator::make($request->all(), [
                'territory' => 'required|string',
                'type' => 'required|in:CLIENT,PRODUCTION,ENCOURS_CREDIT,COLLECT,DEPOT_GARANTIE,EPARGNE_SIMPLE,EPARGNE_PROJET,VOLUME_DAT',
                'period' => 'required|in:month,quarter,year',
                'year' => 'required|integer|min:2020|max:2100',
                'month' => 'nullable|integer|min:1|max:12',
                'quarter' => 'nullable|integer|min:1|max:4',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Données invalides',
                    'errors' => $validator->errors()
                ], 422);
            }

            $data = $validator->validated();

            // Récupérer l'objectif DGA validé pour ce territoire
            $objective = Objective::where('category', 'TERRITOIRE')
                ->where('type', $data['type'])
                ->where('agency_code', $data['territory']) // Le DGA stocke le territoire dans agency_code
                ->where('year', $data['year'])
                ->where(function($query) use ($data) {
                    if ($data['period'] === 'month' && $data['month']) {
                        $query->where('period', 'month')->where('month', $data['month']);
                    } elseif ($data['period'] === 'quarter' && $data['quarter']) {
                        $query->where('period', 'quarter')->where('quarter', $data['quarter']);
                    } elseif ($data['period'] === 'year') {
                        $query->where('period', 'year');
                    }
                })
                ->whereHas('creator', function($q) {
                    $q->whereHas('profile', function($q2) {
                        $q2->where('code', 'DGA');
                    });
                })
                ->where('status', 'validated') // Seulement les objectifs validés
                ->orderBy('created_at', 'desc')
                ->first();

            if ($objective) {
                return response()->json([
                    'success' => true,
                    'data' => [
                        'value' => $objective->value,
                        'description' => $objective->description,
                        'objective_id' => $objective->id
                    ]
                ]);
            }

            return response()->json([
                'success' => false,
                'message' => 'Aucun objectif DGA validé trouvé pour ce territoire et cette période'
            ], 404);

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération de l\'objectif DGA: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Erreur lors de la récupération de l\'objectif DGA'
            ], 500);
        }
    }

    /**
     * Supprime un objectif dans la base de données Laravel
     */
    public function destroy($id): JsonResponse
    {
        try {
            $objective = Objective::find($id);
            
            if (!$objective) {
                return response()->json([
                    'success' => false,
                    'message' => 'Objectif non trouvé'
                ], 404);
            }
            
            $objective->delete();
            
            Log::info('Objectif supprimé avec succès', ['id' => $id]);

            return response()->json([
                'success' => true,
                'message' => 'Objectif supprimé avec succès'
            ]);

        } catch (\Exception $e) {
            Log::error('Erreur lors de la suppression de l\'objectif: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Erreur lors de la suppression de l\'objectif'
            ], 500);
        }
    }
    
    /**
     * Récupère les objectifs en attente de validation selon le profil
     */
    public function pendingValidation(Request $request): JsonResponse
    {
        try {
            $user = Auth::user();
            if (!$user) {
                return response()->json([
                    'success' => false,
                    'message' => 'Utilisateur non authentifié'
                ], 401);
            }

            $profileCode = $user->profile->code ?? null;
            $query = Objective::pendingValidation()->with(['creator', 'validator']);

            // Filtrer selon le profil
            switch ($profileCode) {
                case 'MD':
                    // MD valide les objectifs créés par DGA pour les territoires
                    $query->where('category', 'TERRITOIRE')
                          ->whereHas('creator', function($q) {
                              $q->whereHas('profile', function($q2) {
                                  $q2->where('code', 'DGA');
                              });
                          });
                    break;
                case 'DGA':
                    // DGA valide les objectifs créés par les Responsables Zone pour les agences (TERRITOIRE inclut l’ex-« point de service »)
                    $query->whereIn('category', ['TERRITOIRE', 'POINT SERVICES', 'GRAND COMPTE'])
                          ->whereHas('creator', function($q) {
                              $q->whereHas('profile', function($q2) {
                                  $q2->where('code', 'RESPONSABLE_ZONE');
                              });
                          });
                    break;
                case 'RESPONSABLE_ZONE':
                    // Responsable Zone valide les objectifs créés par les Chefs d'Agence
                    $query->whereHas('creator', function($q) {
                        $q->whereHas('profile', function($q2) {
                            $q2->where('code', 'CHEF_AGENCE');
                        });
                    });
                    break;
                case 'ADMIN':
                    // Admin voit tous les objectifs en attente
                    break;
                default:
                    return response()->json([
                        'success' => false,
                        'message' => 'Vous n\'avez pas la permission de voir les objectifs en attente'
                    ], 403);
            }

            $objectives = $query->orderBy('created_at', 'desc')->get();

            return response()->json([
                'success' => true,
                'data' => $objectives
            ]);
        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération des objectifs en attente: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Erreur lors de la récupération des objectifs en attente'
            ], 500);
        }
    }

    /**
     * Valide un objectif
     */
    public function validateObjective(Request $request, $id): JsonResponse
    {
        try {
            $user = Auth::user();
            if (!$user) {
                return response()->json([
                    'success' => false,
                    'message' => 'Utilisateur non authentifié'
                ], 401);
            }

            $objective = Objective::find($id);
            if (!$objective) {
                return response()->json([
                    'success' => false,
                    'message' => 'Objectif non trouvé'
                ], 404);
            }

            if ($objective->status !== 'pending_validation') {
                return response()->json([
                    'success' => false,
                    'message' => 'Cet objectif n\'est pas en attente de validation'
                ], 400);
            }

            $profileCode = $user->profile->code ?? null;
            $canValidate = false;

            // Vérifier les permissions de validation selon le profil
            switch ($profileCode) {
                case 'MD':
                    // MD valide les objectifs créés par DGA pour les zones
                    $canValidate = $objective->category === 'TERRITOIRE' && 
                                  $objective->creator && 
                                  $objective->creator->profile->code === 'DGA';
                    break;
                case 'DGA':
                    // DGA valide les objectifs créés par les Responsables Zone
                    $canValidate = in_array($objective->category, ['TERRITOIRE', 'POINT SERVICES', 'GRAND COMPTE']) &&
                                  $objective->creator &&
                                  $objective->creator->profile->code === 'RESPONSABLE_ZONE';
                    break;
                case 'RESPONSABLE_ZONE':
                    // Responsable Zone valide les objectifs créés par les Chefs d'Agence
                    $canValidate = $objective->creator &&
                                  $objective->creator->profile->code === 'CHEF_AGENCE';
                    break;
                case 'ADMIN':
                    $canValidate = true;
                    break;
            }

            if (!$canValidate) {
                return response()->json([
                    'success' => false,
                    'message' => 'Vous n\'avez pas la permission de valider cet objectif'
                ], 403);
            }

            $objective->update([
                'status' => 'validated',
                'validated_by' => $user->id,
                'validated_at' => now()
            ]);

            Log::info('Objectif validé', [
                'objective_id' => $id,
                'validator' => $user->id,
                'profile' => $profileCode
            ]);

            return response()->json([
                'success' => true,
                'message' => 'Objectif validé avec succès',
                'data' => $objective->load(['creator', 'validator'])
            ]);
        } catch (\Exception $e) {
            Log::error('Erreur lors de la validation de l\'objectif: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Erreur lors de la validation de l\'objectif'
            ], 500);
        }
    }

    /**
     * Rejette un objectif
     */
    public function reject(Request $request, $id): JsonResponse
    {
        $validator = Validator::make($request->all(), [
            'rejection_reason' => 'required|string|max:500'
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Données invalides',
                'errors' => $validator->errors()
            ], 422);
        }

        try {
            $user = Auth::user();
            if (!$user) {
                return response()->json([
                    'success' => false,
                    'message' => 'Utilisateur non authentifié'
                ], 401);
            }

            $objective = Objective::find($id);
            if (!$objective) {
                return response()->json([
                    'success' => false,
                    'message' => 'Objectif non trouvé'
                ], 404);
            }

            if ($objective->status !== 'pending_validation') {
                return response()->json([
                    'success' => false,
                    'message' => 'Cet objectif n\'est pas en attente de validation'
                ], 400);
            }

            $profileCode = $user->profile->code ?? null;
            $canReject = false;

            // Mêmes permissions que pour la validation
            switch ($profileCode) {
                case 'MD':
                    // MD peut rejeter les objectifs créés par DGA pour les territoires
                    $canReject = $objective->category === 'TERRITOIRE' && 
                                $objective->creator && 
                                $objective->creator->profile->code === 'DGA';
                    break;
                case 'DGA':
                    // DGA peut rejeter les objectifs créés par les Responsables Zone pour les agences
                    $canReject = in_array($objective->category, ['TERRITOIRE', 'POINT SERVICES', 'GRAND COMPTE']) &&
                                $objective->creator &&
                                $objective->creator->profile->code === 'RESPONSABLE_ZONE';
                    break;
                case 'RESPONSABLE_ZONE':
                    // Responsable Zone peut rejeter les objectifs créés par les Chefs d'Agence
                    $canReject = $objective->creator &&
                                $objective->creator->profile->code === 'CHEF_AGENCE';
                    break;
                case 'ADMIN':
                    $canReject = true;
                    break;
            }

            if (!$canReject) {
                return response()->json([
                    'success' => false,
                    'message' => 'Vous n\'avez pas la permission de rejeter cet objectif'
                ], 403);
            }

            $objective->update([
                'status' => 'rejected',
                'validated_by' => $user->id,
                'validated_at' => now(),
                'rejection_reason' => $request->input('rejection_reason')
            ]);

            Log::info('Objectif rejeté', [
                'objective_id' => $id,
                'validator' => $user->id,
                'profile' => $profileCode,
                'reason' => $request->input('rejection_reason')
            ]);

            return response()->json([
                'success' => true,
                'message' => 'Objectif rejeté',
                'data' => $objective->load(['creator', 'validator'])
            ]);
        } catch (\Exception $e) {
            Log::error('Erreur lors du rejet de l\'objectif: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Erreur lors du rejet de l\'objectif'
            ], 500);
        }
    }

    /**
     * Route de test pour vérifier la fusion des objectifs
     */
    public function testMerge(Request $request): JsonResponse
    {
        try {
            $year = $request->input('year', date('Y'));
            $month = $request->input('month', date('n'));
            
            $objectives = Objective::where('type', 'CLIENT')
                ->where('year', $year)
                ->where(function($q) use ($month) {
                    $q->where(function($q2) use ($month) {
                        $q2->where('period', 'month')->where('month', $month);
                    })
                    ->orWhere('period', 'quarter')
                    ->orWhere('period', 'year');
                })
                ->get();
            
            return response()->json([
                'success' => true,
                'objectives' => $objectives,
                'count' => $objectives->count(),
                'year' => $year,
                'month' => $month
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => $e->getMessage()
            ], 500);
        }
    }
    
    /**
     * Route de débogage pour voir les agences et objectifs
     */
    public function debugAgencies(Request $request): JsonResponse
    {
        try {
            $objectives = Objective::all();
            
            // Récupérer un échantillon de données Oracle
            $dataController = new \App\Http\Controllers\DataController($this->oracleService);
            $request->merge([
                'period' => 'month',
                'month' => date('n'),
                'year' => date('Y')
            ]);
            
            $oracleData = $dataController->getClientsData($request);
            $oracleDataArray = json_decode($oracleData->getContent(), true);
            
            // Extraire les noms d'agences depuis Oracle
            $oracleAgencies = [];
            $extractAgencies = function($data, &$agencies, $depth = 0) use (&$extractAgencies) {
                if (is_array($data)) {
                    foreach ($data as $key => $value) {
                        if (is_array($value)) {
                            $name = $value['name'] ?? $value['AGENCE'] ?? $value['NOM_AGENCE'] ?? null;
                            $code = $value['code'] ?? $value['CODE_AGENCE'] ?? null;
                            if ($name || $code) {
                                $agencies[] = [
                                    'name' => strtoupper(trim($name ?? '')),
                                    'code' => strtoupper(trim($code ?? '')),
                                    'objectif_oracle' => $value['objectif'] ?? $value['OBJECTIF_CLIENT'] ?? null,
                                    'depth' => $depth
                                ];
                            }
                            if (isset($value['agencies']) && is_array($value['agencies'])) {
                                $extractAgencies($value['agencies'], $agencies, $depth + 1);
                            }
                            $extractAgencies($value, $agencies, $depth + 1);
                        }
                    }
                }
            };
            
            if (isset($oracleDataArray['hierarchicalData'])) {
                $extractAgencies($oracleDataArray['hierarchicalData'], $oracleAgencies);
            }
            
            return response()->json([
                'success' => true,
                'objectives' => $objectives->map(function($obj) {
                    return [
                        'id' => $obj->id,
                        'type' => $obj->type,
                        'agency_code' => strtoupper(trim($obj->agency_code)),
                        'agency_name' => strtoupper(trim($obj->agency_name ?? '')),
                        'value' => $obj->value,
                        'year' => $obj->year,
                        'month' => $obj->month
                    ];
                })->values(),
                'oracle_agencies_sample' => array_slice($oracleAgencies, 0, 20),
                'oracle_agencies_count' => count($oracleAgencies),
                'matching_suggestions' => $objectives->map(function($obj) use ($oracleAgencies) {
                    $objCode = strtoupper(trim($obj->agency_code));
                    $objName = strtoupper(trim($obj->agency_name ?? ''));
                    $matches = [];
                    
                    foreach ($oracleAgencies as $oracle) {
                        $oracleName = $oracle['name'];
                        $oracleCode = $oracle['code'];
                        
                        if ($objCode === $oracleName || $objCode === $oracleCode ||
                            $objName === $oracleName || $objName === $oracleCode ||
                            stripos($oracleName, $objCode) !== false ||
                            stripos($objCode, $oracleName) !== false) {
                            $matches[] = $oracle;
                        }
                    }
                    
                    return [
                        'objective' => [
                            'code' => $objCode,
                            'name' => $objName
                        ],
                        'matches' => $matches
                    ];
                })
            ]);
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => $e->getMessage(),
                'trace' => $e->getTraceAsString()
            ], 500);
        }
    }

    /**
     * Récupère l'objectif d'une agence pour un type, période et année donnés
     * Utilisé par CHEF_AGENCE pour voir les objectifs déjà fixés pour son agence
     */
    public function getAgencyObjectives(Request $request): JsonResponse
    {
        try {
            $user = Auth::user();
            if (!$user) {
                return response()->json([
                    'success' => false,
                    'message' => 'Utilisateur non authentifié'
                ], 401);
            }

            $validator = Validator::make($request->all(), [
                'type' => 'required|in:CLIENT,PRODUCTION,ENCOURS_CREDIT,COLLECT,DEPOT_GARANTIE,EPARGNE_SIMPLE,EPARGNE_PROJET,VOLUME_DAT',
                'period' => 'required|in:month,quarter,year',
                'year' => 'required|integer|min:2020|max:2100',
                'month' => 'nullable|integer|min:1|max:12',
                'quarter' => 'nullable|integer|min:1|max:4',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Données invalides',
                    'errors' => $validator->errors()
                ], 422);
            }

            $data = $validator->validated();

            // Récupérer l'agence de l'utilisateur
            $user = $user->load('agency');
            if (!$user->agency) {
                return response()->json([
                    'success' => false,
                    'message' => 'Agence non trouvée pour cet utilisateur'
                ], 404);
            }

            $agencyCode = $user->agency->code;

            // Construire la requête pour trouver l'objectif
            // Récupérer tous les objectifs de l'agence (validés ou en attente) pour que le CHEF_AGENCE puisse voir ses objectifs
            $query = Objective::where('type', $data['type'])
                ->where('agency_code', $agencyCode)
                ->where('year', $data['year'])
                ->where(function($q) use ($data) {
                    if ($data['period'] === 'month' && isset($data['month'])) {
                        $q->where(function($q2) use ($data) {
                            $q2->where('period', 'month')->where('month', $data['month']);
                        })
                        ->orWhere('period', 'quarter')
                        ->orWhere('period', 'year');
                    } elseif ($data['period'] === 'quarter' && isset($data['quarter'])) {
                        $q->where(function($q2) use ($data) {
                            $q2->where('period', 'quarter')->where('quarter', $data['quarter']);
                        })
                        ->orWhere('period', 'year');
                    } elseif ($data['period'] === 'year') {
                        $q->where('period', 'year');
                    }
                })
                ->whereIn('status', ['validated', 'pending_validation']) // Objectifs validés ou en attente
                ->orderBy('created_at', 'desc');

            $objective = $query->first();

            if ($objective) {
                $responseData = [
                    'value' => $objective->value,
                    'value_nombres' => $objective->value_nombres,
                    'value_volume' => $objective->value_volume,
                    'description' => $objective->description,
                    'objective_id' => $objective->id
                ];

                return response()->json([
                    'success' => true,
                    'data' => $responseData
                ]);
            }

            return response()->json([
                'success' => false,
                'message' => 'Aucun objectif trouvé pour cette agence et cette période'
            ], 404);

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération de l\'objectif de l\'agence: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Erreur lors de la récupération de l\'objectif de l\'agence'
            ], 500);
        }
    }

    /**
     * Récupère la somme des objectifs des agences d'un territoire pour un type, période et année donnés
     * Utilisé par RESPONSABLE_ZONE pour voir combien d'objectif DGA a déjà été distribué
     */
    public function getAgencyObjectivesSum(Request $request): JsonResponse
    {
        try {
            $validator = Validator::make($request->all(), [
                'territory' => 'required|string',
                'type' => 'required|in:CLIENT,PRODUCTION,ENCOURS_CREDIT,COLLECT,DEPOT_GARANTIE,EPARGNE_SIMPLE,EPARGNE_PROJET,VOLUME_DAT',
                'period' => 'required|in:month,quarter,year',
                'year' => 'required|integer|min:2020|max:2100',
                'month' => 'nullable|integer|min:1|max:12',
                'quarter' => 'nullable|integer|min:1|max:4',
            ]);

            if ($validator->fails()) {
                return response()->json([
                    'success' => false,
                    'message' => 'Données invalides',
                    'errors' => $validator->errors()
                ], 422);
            }

            $data = $validator->validated();

            // Récupérer toutes les agences du territoire
            $territory = Territory::where('code', $data['territory'])
                ->orWhere('name', $data['territory'])
                ->first();

            if (!$territory) {
                return response()->json([
                    'success' => false,
                    'message' => 'Territoire non trouvé'
                ], 404);
            }

            // Récupérer les codes des agences du territoire
            $agencyCodes = Agency::where('territory_id', $territory->id)
                ->pluck('code')
                ->toArray();

            if (empty($agencyCodes)) {
                return response()->json([
                    'success' => true,
                    'data' => $data['type'] === 'PRODUCTION' 
                        ? ['value_nombres' => 0, 'value_volume' => 0]
                        : ['value' => 0]
                ]);
            }

            // Construire la requête pour trouver les objectifs des agences du territoire
            $query = Objective::where('type', $data['type'])
                ->whereIn('agency_code', $agencyCodes)
                ->where('year', $data['year'])
                ->where(function($q) use ($data) {
                    if ($data['period'] === 'month' && isset($data['month'])) {
                        $q->where(function($q2) use ($data) {
                            $q2->where('period', 'month')->where('month', $data['month']);
                        })
                        ->orWhere('period', 'quarter')
                        ->orWhere('period', 'year');
                    } elseif ($data['period'] === 'quarter' && isset($data['quarter'])) {
                        $q->where(function($q2) use ($data) {
                            $q2->where('period', 'quarter')->where('quarter', $data['quarter']);
                        })
                        ->orWhere('period', 'year');
                    } elseif ($data['period'] === 'year') {
                        $q->where('period', 'year');
                    }
                })
                ->where('status', 'validated'); // Seulement les objectifs validés

            $objectives = $query->get();

            if ($data['type'] === 'PRODUCTION') {
                // Pour PRODUCTION, additionner value_nombres et value_volume séparément
                $sumNombres = $objectives->sum('value_nombres') ?? 0;
                $sumVolume = $objectives->sum('value_volume') ?? 0;
                
                return response()->json([
                    'success' => true,
                    'data' => [
                        'value_nombres' => (int)$sumNombres,
                        'value_volume' => (int)$sumVolume
                    ]
                ]);
            } else {
                // Pour les autres types, additionner value
                $sum = $objectives->sum('value') ?? 0;
                
                return response()->json([
                    'success' => true,
                    'data' => [
                        'value' => (int)$sum
                    ]
                ]);
            }

        } catch (\Exception $e) {
            Log::error('Erreur lors de la récupération de la somme des objectifs des agences: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'message' => 'Erreur lors de la récupération de la somme des objectifs des agences'
            ], 500);
        }
    }
    
}
