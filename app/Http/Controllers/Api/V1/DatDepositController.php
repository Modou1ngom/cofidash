<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Services\Vue360\Vue360ApiService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class DatDepositController extends Controller
{
    public function __construct(
        private readonly Vue360ApiService $api
    ) {}

    public function index(Request $request): JsonResponse
    {
        $result = $this->api->datDeposits($request->user());

        if (!$result['success']) {
            return response()->json(['message' => $result['message'] ?? 'Erreur serveur'], 500);
        }

        $payload = $result['data'];

        return response()->json(is_array($payload) && array_key_exists('data', $payload) ? $payload : ['data' => $payload ?? []]);
    }
}
