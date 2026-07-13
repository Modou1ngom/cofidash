<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Services\Vue360\Vue360ApiService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class DashboardController extends Controller
{
    public function __construct(
        private readonly Vue360ApiService $api
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
            return response()->json(['message' => $result['message'] ?? 'Erreur serveur'], 500);
        }

        $payload = $result['data'];

        return response()->json(is_array($payload) && array_key_exists('data', $payload) ? $payload : ['data' => $payload]);
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
