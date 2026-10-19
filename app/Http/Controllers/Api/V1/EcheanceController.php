<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Services\Vue360\Vue360ApiService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class EcheanceController extends Controller
{
    public function __construct(
        private readonly Vue360ApiService $api
    ) {}

    public function index(Request $request): JsonResponse
    {
        $cafCode = $request->query('caf_code');
        $agency = $request->query('agency');
        $search = $request->query('q');
        $result = $this->api->echeances(
            $request->user(),
            $this->optionalInt($request, 'year'),
            $this->optionalInt($request, 'month'),
            is_string($cafCode) ? $cafCode : null,
            is_string($agency) ? $agency : null,
            is_string($search) ? $search : null,
        );

        return $this->respondList($result);
    }

    public function show(Request $request, string $id): JsonResponse
    {
        $result = $this->api->echeance(
            $request->user(),
            $id,
            $this->optionalInt($request, 'year'),
            $this->optionalInt($request, 'month'),
        );

        if (! $result['success']) {
            return response()->json([
                'message' => $result['message'] ?? 'Échéance introuvable',
            ], $result['status'] ?? 404);
        }

        return response()->json(['data' => $result['data']]);
    }

    private function optionalInt(Request $request, string $key): ?int
    {
        $value = $request->query($key);
        if ($value === null || $value === '') {
            return null;
        }

        return (int) $value;
    }

    private function respondList(array $result): JsonResponse
    {
        if (! $result['success']) {
            return response()->json([
                'message' => $result['message'] ?? 'Erreur serveur',
            ], $result['status'] ?? 500);
        }

        $payload = $result['data'];

        return response()->json(is_array($payload) && array_key_exists('data', $payload) ? $payload : ['data' => $payload ?? []]);
    }
}
