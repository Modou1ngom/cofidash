<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Services\CafLocalObjectiveService;
use App\Services\Vue360\Vue360ApiService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class DashboardController extends Controller
{
    public function __construct(
        private readonly Vue360ApiService $api,
        private readonly CafLocalObjectiveService $cafObjectives,
    ) {}

    public function kpis(Request $request): JsonResponse
    {
        $result = $this->api->dashboardKpis($request->user());

        if (!$result['success']) {
            return response()->json(['message' => $result['message'] ?? 'Erreur serveur'], 500);
        }

        $payload = $result['data'];

        return response()->json(is_array($payload) && array_key_exists('data', $payload) ? $payload : ['data' => $payload]);
    }

    public function cafOverview(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'caf_code' => 'nullable|string|max:32',
            'month' => 'nullable|integer|min:1|max:12',
            'year' => 'nullable|integer|min:2000|max:2100',
        ]);

        $result = $this->api->cafVueEnsemble(
            $request->user(),
            $validated['caf_code'] ?? null,
            isset($validated['month']) ? (int) $validated['month'] : null,
            isset($validated['year']) ? (int) $validated['year'] : null,
        );

        if (!$result['success']) {
            $message = $result['message'] ?? 'Erreur serveur';
            if (is_array($message)) {
                $message = $message['detail'] ?? json_encode($message, JSON_UNESCAPED_UNICODE);
            }

            return response()->json([
                'message' => is_string($message) && $message !== ''
                    ? $message
                    : 'Impossible de charger le portefeuille CAF.',
            ], $result['status'] ?? 500);
        }

        $payload = $result['data'];
        $wrapped = is_array($payload) && array_key_exists('data', $payload);
        $data = $wrapped ? $payload['data'] : $payload;

        if (is_array($data)) {
            $month = isset($validated['month']) ? (int) $validated['month'] : (int) now()->month;
            $year = isset($validated['year']) ? (int) $validated['year'] : (int) now()->year;
            $data = $this->injectLocalProductionObjectives($request, $data, $month, $year);
        }

        return response()->json($wrapped ? ['data' => $data] : ['data' => $data]);
    }

    /**
     * Objectifs production fixés par le CA (table locale `objectives`), pas DASH.
     *
     * @param  array<string, mixed>  $data
     * @return array<string, mixed>
     */
    private function injectLocalProductionObjectives(
        Request $request,
        array $data,
        int $month,
        int $year,
    ): array {
        $objectives = $this->cafObjectives->productionObjectivesForUser(
            $request->user(),
            $month,
            $year,
        );

        $production = is_array($data['production'] ?? null) ? $data['production'] : [];
        $loanCount = (float) ($production['loan_count'] ?? 0);
        $volume = (float) ($production['monthly_volume'] ?? 0);
        $loanObj = (float) $objectives['loan_count_objective'];
        $volumeObj = (float) $objectives['monthly_volume_objective'];

        $production['loan_count_objective'] = $loanObj;
        $production['monthly_volume_objective'] = $volumeObj;
        $production['loan_count_realization_pct'] = $loanObj > 0
            ? round(($loanCount / $loanObj) * 100, 1)
            : 0.0;
        $production['monthly_volume_realization_pct'] = $volumeObj > 0
            ? round(($volume / $volumeObj) * 100, 1)
            : 0.0;

        $data['production'] = $production;

        return $data;
    }

    public function cafManagers(Request $request): JsonResponse
    {
        $result = $this->api->cafManagers();
        if (!$result['success']) {
            return response()->json(
                ['message' => $result['message'] ?? 'Impossible de charger les gestionnaires'],
                $result['status'] ?? 500
            );
        }

        return response()->json($result['data']);
    }
}
