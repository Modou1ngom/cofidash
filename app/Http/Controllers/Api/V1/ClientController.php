<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Services\Vue360\CheckingPiRules;
use App\Services\Vue360\Vue360ApiService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ClientController extends Controller
{
    public function __construct(
        private readonly Vue360ApiService $api
    ) {}

    public function index(Request $request): JsonResponse
    {
        $field = $request->query('field');
        $query = $request->query('query');

        if ($field && !$query) {
            return response()->json(['message' => 'Le paramètre query est requis avec field'], 422);
        }

        $result = $this->api->clients($request->user(), $field, $query);

        return $this->respond($result);
    }

    public function show(Request $request, string $id): JsonResponse
    {
        $refresh = filter_var($request->query('refresh', false), FILTER_VALIDATE_BOOLEAN);
        $result = $this->api->client($request->user(), $id, $refresh);

        if (!$result['success']) {
            return $this->respond($result, 404);
        }

        $payload = $result['data'];
        $client = is_array($payload) ? ($payload['data'] ?? $payload) : $payload;

        return response()->json(['data' => $client]);
    }

    public function kyc(Request $request, string $id): JsonResponse
    {
        $result = $this->api->clientKyc($request->user(), $id);

        if (!$result['success']) {
            return $this->respond($result, 404);
        }

        $payload = $result['data'];
        $kyc = is_array($payload) ? ($payload['data'] ?? $payload) : $payload;

        return response()->json(['data' => $kyc]);
    }

    public function checkingPi(Request $request, string $id): JsonResponse
    {
        $result = $this->api->clientCheckingPi($request->user(), $id);

        if (!$result['success']) {
            return $this->respond($result, 404);
        }

        $payload = $result['data'];
        $data = is_array($payload) ? ($payload['data'] ?? $payload) : $payload;
        if (! is_array($data)) {
            $data = [];
        }

        return response()->json(['data' => CheckingPiRules::apply($data)]);
    }

    public function accounts(Request $request, string $id): JsonResponse
    {
        $refresh = filter_var($request->query('refresh', false), FILTER_VALIDATE_BOOLEAN);
        $result = $this->api->clientAccounts(
            $request->user(),
            $id,
            $request->query('type'),
            $refresh,
        );

        if (!$result['success']) {
            return $this->respond($result, ($result['status'] ?? 0) === 422 ? 422 : 500);
        }

        $payload = $result['data'];
        $data = is_array($payload) ? ($payload['data'] ?? $payload) : $payload;

        return response()->json(['data' => $data]);
    }

    public function account(Request $request, string $id, string $accountNo): JsonResponse
    {
        $refresh = filter_var($request->query('refresh', false), FILTER_VALIDATE_BOOLEAN);
        $result = $this->api->clientAccount(
            $request->user(),
            $id,
            $accountNo,
            $refresh,
            (int) $request->query('transactions_limit', 20),
        );

        if (!$result['success']) {
            return $this->respond($result, 404);
        }

        $payload = $result['data'];
        $account = is_array($payload) ? ($payload['data'] ?? $payload) : $payload;

        return response()->json(['data' => $account]);
    }

    private function respond(array $result, int $errorStatus = 500): JsonResponse
    {
        if ($result['success']) {
            $payload = $result['data'];

            return response()->json(is_array($payload) && array_key_exists('data', $payload) ? $payload : ['data' => $payload ?? []]);
        }

        $status = ($result['status'] ?? 0) === 404 ? 404 : $errorStatus;

        return response()->json([
            'message' => $result['message'] ?? 'Erreur serveur',
        ], $status);
    }
}
