<?php

namespace App\Http\Controllers;

use App\Models\ReferenceCompteBloc;
use App\Models\ReferenceCompteGl;
use App\Models\ReferenceCompteRubrique;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Schema;

class ReferenceCompteController extends Controller
{
    /**
     * Liste tous les blocs avec leurs rubriques et GL.
     */
    public function index(): JsonResponse
    {
        try {
            $blocs = ReferenceCompteBloc::with(['rubriques.gls'])
                ->orderBy('sort_order')
                ->get()
                ->map(function ($bloc) {
                    return [
                        'id' => $bloc->id,
                        'libelle' => $bloc->libelle,
                        'cle_repartition_nom' => $bloc->cle_repartition_nom ?? '',
                        'cle_repartition' => $this->getCleRepartitionForBloc($bloc->id),
                        'rubriques' => $bloc->rubriques->map(function ($rubrique) {
                            return [
                                'id' => $rubrique->id,
                                'libelle' => $rubrique->libelle,
                                'gls' => $rubrique->gls->map(fn ($gl) => [
                                    'id' => $gl->id,
                                    'numero_gl' => $gl->numero_gl,
                                    'nom_gl' => $gl->nom_gl,
                                ])->values()->all(),
                            ];
                        })->values()->all(),
                    ];
                });

            return response()->json(['data' => $blocs]);
        } catch (\Exception $e) {
            Log::error('ReferenceCompte index: ' . $e->getMessage());
            return response()->json([
                'error' => 'Erreur lors du chargement',
                'message' => $e->getMessage(),
            ], 500);
        }
    }

    /**
     * Enregistre les blocs, rubriques et GL (remplace tout).
     */
    public function store(Request $request): JsonResponse
    {
        $request->validate([
            'blocs' => 'required|array',
            'blocs.*.libelle' => 'required|string|max:255',
            'blocs.*.cle_repartition_nom' => 'nullable|string|max:255',
            'blocs.*.cle_repartition' => 'nullable|array',
            'blocs.*.cle_repartition.*' => 'nullable|numeric',
            'blocs.*.rubriques' => 'array',
            'blocs.*.rubriques.*.libelle' => 'required|string|max:255',
            'blocs.*.rubriques.*.gls' => 'array',
            'blocs.*.rubriques.*.gls.*.numero_gl' => 'required|string|max:50',
            'blocs.*.rubriques.*.gls.*.nom_gl' => 'nullable|string',
        ]);

        try {
            DB::transaction(function () use ($request) {
                ReferenceCompteGl::query()->delete();
                ReferenceCompteRubrique::query()->delete();
                ReferenceCompteBloc::query()->delete();

                foreach ($request->input('blocs', []) as $blocOrder => $b) {
                    $bloc = ReferenceCompteBloc::create([
                        'libelle' => $b['libelle'],
                        'sort_order' => $blocOrder,
                        'cle_repartition_nom' => isset($b['cle_repartition_nom']) && trim((string) $b['cle_repartition_nom']) !== '' ? trim($b['cle_repartition_nom']) : null,
                    ]);

                    foreach (array_values($b['rubriques'] ?? []) as $rubOrder => $r) {
                        $rubrique = ReferenceCompteRubrique::create([
                            'bloc_id' => $bloc->id,
                            'libelle' => $r['libelle'],
                            'sort_order' => $rubOrder,
                        ]);

                        foreach (array_values($r['gls'] ?? []) as $glOrder => $g) {
                            if (empty($g['numero_gl'])) {
                                continue;
                            }
                            ReferenceCompteGl::create([
                                'rubrique_id' => $rubrique->id,
                                'numero_gl' => $g['numero_gl'],
                                'nom_gl' => $g['nom_gl'] ?? null,
                                'sort_order' => $glOrder,
                            ]);
                        }
                    }

                    if (Schema::hasTable('reference_compte_cle_repartition')) {
                        $this->storeCleRepartitionForBloc($bloc->id, $b['cle_repartition'] ?? []);
                    }
                }
            });

            return response()->json([
                'success' => true,
                'message' => 'Référence compte enregistrée avec succès.',
            ]);
        } catch (\Exception $e) {
            Log::error('ReferenceCompte store: ' . $e->getMessage());
            return response()->json([
                'success' => false,
                'error' => 'Erreur lors de l\'enregistrement',
                'message' => $e->getMessage(),
            ], 500);
        }
    }

    /** Clés d'entités (agences) utilisées dans le CR par agence. */
    private static function cleRepartitionEntityKeys(): array
    {
        return [
            'siege', 'grand_compte',
            'point_e', 'castors', 'lamine_gueye', 'maristes', 'scat_urbam',
            'niarry_talli', 'linguerla', 'parcelles', 'pikine', 'rufisque',
            'thies', 'kaolack', 'mbour', 'tambacounda', 'ziguinchor',
            'touba', 'saint_louis', 'diourbel', 'louga', 'ourossogui',
        ];
    }

    private function getCleRepartitionForBloc(int $blocId): array
    {
        $keys = self::cleRepartitionEntityKeys();
        if (! Schema::hasTable('reference_compte_cle_repartition')) {
            return array_combine($keys, array_fill(0, count($keys), 0));
        }
        $rows = DB::table('reference_compte_cle_repartition')
            ->where('bloc_id', $blocId)
            ->get()
            ->keyBy('entity_key');
        $out = [];
        foreach ($keys as $k) {
            $out[$k] = isset($rows[$k]) ? (float) $rows[$k]->value : 0;
        }
        return $out;
    }

    private function storeCleRepartitionForBloc(int $blocId, array $cleRepartition): void
    {
        if (! Schema::hasTable('reference_compte_cle_repartition')) {
            return;
        }
        DB::table('reference_compte_cle_repartition')->where('bloc_id', $blocId)->delete();
        $keys = self::cleRepartitionEntityKeys();
        $now = now();
        foreach ($keys as $entityKey) {
            $value = isset($cleRepartition[$entityKey]) ? (float) $cleRepartition[$entityKey] : 0;
            DB::table('reference_compte_cle_repartition')->insert([
                'bloc_id' => $blocId,
                'entity_key' => $entityKey,
                'value' => $value,
                'created_at' => $now,
                'updated_at' => $now,
            ]);
        }
    }
}
