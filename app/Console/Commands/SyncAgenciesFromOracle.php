<?php

namespace App\Console\Commands;

use App\Models\Agency;
use App\Models\Territory;
use App\Models\User;
use App\Services\OracleService;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Log;

class SyncAgenciesFromOracle extends Command
{
    /**
     * The name and signature of the console command.
     *
     * @var string
     */
    protected $signature = 'agencies:sync-from-oracle
                            {--prune : Supprimer les agences dont le code n\'est pas dans Oracle (détache les utilisateurs)}';

    /**
     * The console command description.
     *
     * @var string
     */
    protected $description = 'Synchronise les agences depuis Oracle vers la base de données Laravel';

    protected $oracleService;

    public function __construct(OracleService $oracleService)
    {
        parent::__construct();
        $this->oracleService = $oracleService;
    }

    /**
     * Execute the console command.
     */
    public function handle()
    {
        $this->info('🔄 Synchronisation des agences depuis Flexcube / STTM_BRANCH (via service Python)...');

        try {
            $this->ensureCanonicalTerritoriesExist();

            $result = $this->oracleService->getAgenciesFromFlexcube();

            if (!$result['success']) {
                $msg = $result['message'] ?? $result['error'] ?? 'Erreur inconnue';
                $this->error('❌ Erreur lors de la récupération des agences: '.$msg);

                return 1;
            }

            $payload = $result['data'] ?? [];
            // Endpoint Python : {"data": [ {code, name, ...}, ... ] }
            // Ancien format (liste nue) encore accepté.
            if (is_array($payload) && array_is_list($payload)) {
                $agencies = $payload;
            } elseif (is_array($payload) && isset($payload['data']) && is_array($payload['data'])) {
                $agencies = $payload['data'];
            } else {
                $this->error('❌ Réponse invalide du service Python (attendu: tableau d\'agences).');
                Log::error('Sync agences: payload invalide', [
                    'keys' => is_array($payload) ? array_keys($payload) : gettype($payload),
                ]);

                return 1;
            }

            if (! array_is_list($agencies)) {
                $agencies = array_values(array_filter($agencies, 'is_array'));
            }

            $this->info('📊 '.count($agencies).' agence(s) reçue(s)');

            if (count($agencies) === 0) {
                $this->error('❌ Aucune agence renvoyée par Oracle/Flexcube. Vérifiez PYTHON_SERVICE_URL et l’endpoint /api/oracle/data/agencies-from-flexcube.');

                return 1;
            }

            $synced = 0;
            $updated = 0;
            $errors = 0;
            $syncedCodes = [];

            foreach ($agencies as $row) {
                if (! is_array($row)) {
                    continue;
                }
                $code = isset($row['code']) ? strtoupper(trim((string) $row['code'])) : '';
                $name = isset($row['name']) ? trim((string) $row['name']) : '';
                $territoryCode = $row['territory_code'] ?? null;
                if ($territoryCode !== null && $territoryCode !== '') {
                    $territoryCode = trim((string) $territoryCode);
                } else {
                    $territoryCode = null;
                }

                if ($code === '' || $name === '') {
                    continue;
                }

                $syncedCodes[$code] = true;

                try {
                    $agency = $this->syncAgency([
                        'code' => $code,
                        'name' => $name,
                        'territory_code' => $territoryCode,
                    ]);
                    if ($agency->wasRecentlyCreated) {
                        $synced++;
                    } else {
                        $updated++;
                    }
                } catch (\Exception $e) {
                    $errors++;
                    $this->warn("⚠️ Erreur pour l'agence {$code}: ".$e->getMessage());
                    Log::error('Erreur synchronisation agence', [
                        'agency' => $row,
                        'error' => $e->getMessage(),
                    ]);
                }
            }

            $this->info('✅ Synchronisation terminée:');
            $this->info("   - {$synced} agence(s) créée(s)");
            $this->info("   - {$updated} agence(s) mise(s) à jour");
            if ($errors > 0) {
                $this->warn("   - {$errors} erreur(s)");
            }

            $codeList = array_keys($syncedCodes);
            if ($this->option('prune') && count($codeList) > 0) {
                $removed = $this->pruneAgenciesNotInOracle($codeList);
                $this->info("   - {$removed} agence(s) supprimée(s) (hors Oracle)");
            }

            return 0;
        } catch (\Exception $e) {
            $this->error('❌ Erreur lors de la synchronisation: '.$e->getMessage());
            Log::error('Erreur synchronisation agences Oracle', [
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            return 1;
        }
    }

    /**
     * Garantit les 4 territoires attendus (liens agence → territoire par code).
     */
    /**
     * Supprime les agences dont le code n'est pas dans la liste Oracle (ex. anciennes lignes de seed).
     */
    private function pruneAgenciesNotInOracle(array $oracleCodes): int
    {
        $toDelete = Agency::whereNotIn('code', $oracleCodes)->pluck('id');
        if ($toDelete->isEmpty()) {
            return 0;
        }

        $ids = $toDelete->all();
        User::whereIn('agency_id', $ids)->update(['agency_id' => null]);
        Agency::whereIn('id', $ids)->update(['chef_agence_user_id' => null]);

        return Agency::whereIn('id', $ids)->delete();
    }

    private function ensureCanonicalTerritoriesExist(): void
    {
        $rows = [
            ['code' => 'DAKAR_VILLE', 'name' => 'Dakar Ville', 'description' => 'Territoire de Dakar Ville'],
            ['code' => 'DAKAR_BANLIEUE', 'name' => 'Dakar Banlieue', 'description' => 'Territoire de Dakar Banlieue'],
            ['code' => 'PROVINCE_CENTRE_SUD', 'name' => 'Province Centre Sud', 'description' => 'Territoire Province Centre Sud'],
            ['code' => 'PROVINCE_NORD', 'name' => 'Province Nord', 'description' => 'Territoire Province Nord'],
        ];
        foreach ($rows as $row) {
            Territory::updateOrCreate(
                ['code' => $row['code']],
                array_merge($row, ['is_active' => true])
            );
        }
    }

    /**
     * Synchronise une agence dans la base de données
     */
    private function syncAgency(array $agencyData): Agency
    {
        $territory = null;
        if (! empty($agencyData['territory_code'])) {
            $territory = Territory::where('code', $agencyData['territory_code'])->first();
        }

        return Agency::updateOrCreate(
            ['code' => $agencyData['code']],
            [
                'name' => $agencyData['name'],
                'territory_id' => $territory?->id,
                'is_active' => true,
            ]
        );
    }
}
