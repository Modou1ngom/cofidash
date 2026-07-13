<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Services\Vue360\Vue360ApiService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class CreditController extends Controller
{
    public function __construct(
        private readonly Vue360ApiService $api
    ) {}

    public function index(Request $request): JsonResponse
    {
        $clientId = $request->query('client_id');
        $result = $this->api->credits($request->user(), $clientId);

        return $this->respondList($result);
    }

    public function show(Request $request, string $id): JsonResponse
    {
        $result = $this->api->credit($request->user(), $id);

        if (!$result['success']) {
            return response()->json(['message' => 'Crédit introuvable'], 404);
        }

        $payload = $result['data'];
        $credit = is_array($payload) ? ($payload['data'] ?? $payload) : $payload;

        return response()->json(['data' => $credit]);
    }

    public function repayments(string $id): JsonResponse
    {
        $result = $this->api->repayments($id);

        return $this->respondList($result);
    }

    public function amortizationSchedule(string $id): JsonResponse
    {
        $result = $this->api->amortizationSchedule($id);

        if (!$result['success']) {
            return response()->json([
                'message' => $result['message'] ?? 'Erreur serveur',
            ], $result['status'] ?? 500);
        }

        $payload = $result['data'];

        return response()->json(is_array($payload) && array_key_exists('data', $payload) ? $payload : ['data' => $payload ?? []]);
    }

    private function respondList(array $result): JsonResponse
    {
        if (!$result['success']) {
            return response()->json([
                'message' => $result['message'] ?? 'Erreur serveur',
            ], $result['status'] ?? 500);
        }

        $payload = $result['data'];

        return response()->json(is_array($payload) && array_key_exists('data', $payload) ? $payload : ['data' => $payload ?? []]);
    }
}
