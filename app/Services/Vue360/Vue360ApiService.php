<?php

namespace App\Services\Vue360;

use App\Models\Agency;
use App\Models\Territory;
use App\Models\User;
use App\Support\UserFacingError;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class Vue360ApiService
{
    private const HTTP_CONNECT_TIMEOUT = 5;

    private const HTTP_TIMEOUT = 45;

    private const HTTP_TIMEOUT_LONG = 120;

    public function __construct(
        private readonly Vue360ScopeService $scope
    ) {}

    private function baseUrl(): string
    {
        return rtrim((string) env('PYTHON_SERVICE_URL', 'http://localhost:8001'), '/');
    }

    /**
     * @param  array<string, mixed>  $params
     * @return array{success: bool, data?: mixed, message?: string, status?: int}
     */
    private function get(string $path, array $params = [], ?int $timeout = null): array
    {
        try {
            $response = Http::timeout($timeout ?? self::HTTP_TIMEOUT)
                ->connectTimeout(self::HTTP_CONNECT_TIMEOUT)
                ->get($this->baseUrl().$path, $params);

            if ($response->successful()) {
                return ['success' => true, 'data' => $response->json()];
            }

            Log::warning('Vue360 Python GET failed', [
                'path' => $path,
                'status' => $response->status(),
                'body' => $response->body(),
            ]);

            return [
                'success' => false,
                'status' => $response->status(),
                'message' => UserFacingError::from(
                    $response->json('detail') ?? $response->body()
                ),
            ];
        } catch (\Throwable $e) {
            Log::error('Vue360 Python GET exception: '.$e->getMessage());

            return [
                'success' => false,
                'status' => 503,
                'message' => UserFacingError::from($e->getMessage()),
            ];
        }
    }

    private function scopedParams(User $user, array $extra = []): array
    {
        $branches = $this->scope->branchCodesQueryParam($this->scope->branchCodesForUser($user));
        if ($branches !== null) {
            $extra['branch_codes'] = $branches;
        }

        return $extra;
    }

    public function clients(User $user, ?string $field = null, ?string $query = null): array
    {
        $params = $this->scopedParams($user);
        if ($query !== null && $query !== '') {
            $params['query'] = $query;
            if ($field) {
                $params['field'] = $field;
            }
        }

        return $this->get('/api/vue360/clients', $params);
    }

    public function client(User $user, string $id, bool $refreshCache = false): array
    {
        $params = $this->scopedParams($user, ['refresh_cache' => $refreshCache ? 'true' : 'false']);

        return $this->get('/api/vue360/clients/'.urlencode($id), $params);
    }

    public function clientKyc(User $user, string $id): array
    {
        $params = $this->scopedParams($user);

        return $this->get('/api/vue360/clients/'.urlencode($id).'/kyc', $params);
    }

    public function clientCheckingPi(User $user, string $id): array
    {
        $params = $this->scopedParams($user);

        return $this->get('/api/vue360/clients/'.urlencode($id).'/checking-pi', $params);
    }

    public function clientAccounts(
        User $user,
        string $id,
        ?string $type = null,
        bool $refresh = false,
    ): array {
        $params = $this->scopedParams($user, [
            'refresh' => $refresh ? 'true' : 'false',
        ]);
        if ($type) {
            $params['type'] = $type;
        }

        return $this->get('/api/vue360/clients/'.urlencode($id).'/accounts', $params);
    }

    public function clientAccount(
        User $user,
        string $id,
        string $accountNo,
        bool $refresh = false,
        int $transactionsLimit = 20,
    ): array {
        $params = $this->scopedParams($user, [
            'refresh' => $refresh ? 'true' : 'false',
            'transactions_limit' => $transactionsLimit,
        ]);

        return $this->get(
            '/api/vue360/clients/'.urlencode($id).'/accounts/'.urlencode($accountNo),
            $params
        );
    }

    public function credits(User $user, ?string $clientId = null, ?string $cafCode = null): array
    {
        $params = $this->scopedParams($user);
        if ($clientId) {
            $params['client_id'] = $clientId;
        }
        $resolvedCode = trim((string) ($cafCode ?: $this->cafCodeForUser($user) ?: ''));
        if ($resolvedCode !== '') {
            $params['caf_code'] = $resolvedCode;
            $params['limit'] = 200;
        }

        return $this->get('/api/vue360/credits', $params);
    }

    public function credit(User $user, string $id): array
    {
        return $this->get('/api/vue360/credits/'.urlencode($id), $this->scopedParams($user));
    }

    public function repayments(string $loanId): array
    {
        return $this->get('/api/vue360/credits/'.urlencode($loanId).'/repayments');
    }

    public function amortizationSchedule(string $loanId): array
    {
        return $this->get('/api/vue360/credits/'.urlencode($loanId).'/ta');
    }

    public function dashboardKpis(User $user): array
    {
        return $this->get('/api/vue360/dashboard/kpis', $this->scopedParams($user));
    }

    public function cafManagers(): array
    {
        return $this->get('/api/vue360/caf/managers');
    }

    /**
     * Vérifie qu'un code gestionnaire existe dans Flexcube.
     *
     * @return array<string, mixed>|null
     */
    public function verifyManagerCode(string $code): ?array
    {
        $result = $this->get('/api/vue360/caf/resolve-manager', [
            'manager_code' => $code,
        ]);
        if (!$result['success']) {
            return null;
        }

        $payload = $result['data']['data'] ?? $result['data'] ?? null;

        return is_array($payload) ? $payload : null;
    }

    public function cafVueEnsemble(
        User $user,
        ?string $cafCode = null,
        ?int $month = null,
        ?int $year = null,
        bool $refresh = false,
    ): array {
        $params = $this->scopedParams($user);
        $resolvedCode = $cafCode ?: $this->cafCodeForUser($user);
        if (!$resolvedCode) {
            return [
                'success' => false,
                'status' => 422,
                'message' => 'Code gestionnaire (GP) requis pour afficher l\'encours CAF.',
            ];
        }
        $params['caf_code'] = $resolvedCode;
        $params['all_dossiers'] = true;
        if ($month !== null) {
            $params['month'] = $month;
        }
        if ($year !== null) {
            $params['year'] = $year;
        }
        if ($refresh) {
            $params['refresh'] = 'true';
        }

        return $this->get('/api/vue360/caf/vue-ensemble', $params, self::HTTP_TIMEOUT_LONG);
    }

    /**
     * Code gestionnaire Flexcube (FIELD_CHAR_2 / LOV GESTION_PRET) du CAF connecté.
     */
    public function cafCodeForUser(User $user): ?string
    {
        $code = trim((string) ($user->manager_code ?? ''));

        return $code !== '' ? $code : null;
    }

    public function risks(User $user): array
    {
        return $this->get('/api/vue360/risks', $this->scopedParams($user));
    }

    public function datDeposits(User $user): array
    {
        return $this->get('/api/vue360/dat-deposits', $this->scopedParams($user));
    }

    public function opportunities(User $user): array
    {
        return $this->get('/api/vue360/opportunities', $this->scopedParams($user));
    }

    public function notifications(User $user): array
    {
        return $this->get('/api/vue360/notifications', $this->scopedParams($user));
    }

    /**
     * POST vers Python sans cache Laravel.
     *
     * @param  array<string, mixed>  $body
     * @return array{success: bool, data?: mixed, message?: string, status?: int}
     */
    private function post(string $path, array $body): array
    {
        try {
            $response = Http::timeout(self::HTTP_TIMEOUT)
                ->connectTimeout(self::HTTP_CONNECT_TIMEOUT)
                ->post($this->baseUrl().$path, $body);

            if ($response->successful()) {
                return ['success' => true, 'data' => $response->json()];
            }

            Log::warning('Vue360 Python POST failed', [
                'path' => $path,
                'status' => $response->status(),
                'body' => $response->body(),
            ]);

            return [
                'success' => false,
                'status' => $response->status(),
                'message' => UserFacingError::from(
                    $response->json('detail') ?? $response->body()
                ),
            ];
        } catch (\Throwable $e) {
            Log::error('Vue360 Python POST exception: '.$e->getMessage());

            return [
                'success' => false,
                'status' => 503,
                'message' => UserFacingError::from($e->getMessage()),
            ];
        }
    }

    /**
     * @return array<int, array<string, mixed>>
     */
    public function agenciesForUser(User $user): array
    {
        $role = $this->scope->mapRole($user->profile?->code);
        $query = Agency::query()->with('territory')->where('is_active', true);

        if (in_array($role, ['chef_agence', 'caf', 'cc'], true)) {
            $agency = $user->agency ?? $user->managedAgency;
            if (!$agency) {
                return [];
            }
            $query->where('id', $agency->id);
        } elseif ($role === 'responsable_zone') {
            $territory = $user->territory ?? $user->responsibleTerritory;
            if (!$territory) {
                return [];
            }
            $query->where('territory_id', $territory->id);
        }

        $agencies = $query->get();
        if ($agencies->isEmpty()) {
            return [];
        }

        $payload = $agencies->map(fn (Agency $a) => [
            'code' => (string) $a->code,
            'name' => $a->name,
            'zone' => $a->territory?->name ?? '',
            'category' => 'agence',
        ])->values()->all();

        $result = $this->post('/api/vue360/agencies/kpis', ['agencies' => $payload]);
        if ($result['success']) {
            $data = $result['data']['data'] ?? $result['data'] ?? [];

            return is_array($data) ? array_values($data) : [];
        }

        Log::warning('Fallback KPI agences sans Oracle', ['message' => $result['message'] ?? null]);

        return $agencies->map(fn (Agency $a) => $this->formatAgencyFallback($a))->values()->all();
    }

    public function agencyForUser(User $user, string $id): ?array
    {
        $agencies = $this->agenciesForUser($user);
        foreach ($agencies as $agency) {
            if (($agency['id'] ?? '') === $id || str_ends_with($id, (string) ($agency['id'] ?? ''))) {
                return $agency;
            }
        }

        return null;
    }

    /**
     * @return array<string, mixed>
     */
    private function formatAgencyFallback(Agency $agency): array
    {
        return [
            'id' => 'AG-'.$agency->code,
            'name' => $agency->name,
            'zone' => $agency->territory?->name ?? '',
            'category' => 'agence',
            'active_clients' => 0,
            'active_credits' => 0,
            'total_outstanding' => 0,
            'savings_collected' => 0,
            'monthly_production' => 0,
            'performance_vs_last_year' => 0,
            'ranking' => 0,
            'encours_evolution' => array_fill(0, 12, 0),
        ];
    }

    /**
     * @return array<int, array<string, mixed>>
     */
    public function zonesForUser(User $user): array
    {
        $role = $this->scope->mapRole($user->profile?->code);
        $query = Territory::query()->with('agencies')->where('is_active', true);

        if ($role === 'responsable_zone') {
            $territory = $user->territory ?? $user->responsibleTerritory;
            if (!$territory) {
                return [];
            }
            $query->where('id', $territory->id);
        } elseif (in_array($role, ['chef_agence', 'caf', 'cc'], true)) {
            $territoryId = $user->agency?->territory_id;
            if (!$territoryId) {
                return [];
            }
            $query->where('id', $territoryId);
        }

        $territories = $query->get();
        if ($territories->isEmpty()) {
            return [];
        }

        $zonesPayload = $territories->map(fn (Territory $t) => [
            'id' => 'ZN-'.$t->code,
            'name' => $t->name,
            'agencies' => $t->agencies->map(fn (Agency $a) => [
                'code' => (string) $a->code,
                'name' => $a->name,
            ])->values()->all(),
        ])->values()->all();

        $agenciesKpis = $this->agenciesForUser($user);
        $result = $this->post('/api/vue360/zones/kpis', [
            'zones' => $zonesPayload,
            'agencies_kpis' => $agenciesKpis,
        ]);

        if ($result['success']) {
            $data = $result['data']['data'] ?? $result['data'] ?? [];

            return is_array($data) ? array_values($data) : [];
        }

        Log::warning('Fallback KPI zones sans Oracle', ['message' => $result['message'] ?? null]);

        return $territories->map(fn (Territory $t) => $this->formatZoneFallback($t))->values()->all();
    }

    public function zoneForUser(User $user, string $id): ?array
    {
        foreach ($this->zonesForUser($user) as $zone) {
            if (($zone['id'] ?? '') === $id) {
                return $zone;
            }
        }

        return null;
    }

    /**
     * @return array<string, mixed>
     */
    private function formatZoneFallback(Territory $territory): array
    {
        $agencies = $territory->agencies ?? collect();

        return [
            'id' => 'ZN-'.$territory->code,
            'name' => $territory->name,
            'active_clients' => 0,
            'active_credits' => 0,
            'total_outstanding' => 0,
            'savings_collected' => 0,
            'agency_count' => $agencies->count(),
            'top_agency' => $agencies->first()?->name ?? '',
            'flop_agency' => $agencies->last()?->name ?? '',
            'encours_evolution' => array_fill(0, 12, 0),
            'agency_rankings' => $agencies->map(fn (Agency $a, int $i) => [
                'agency_name' => $a->name,
                'score' => 0,
                'outstanding' => 0,
                'rank' => $i + 1,
            ])->values()->all(),
        ];
    }
}
