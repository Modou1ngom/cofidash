<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Services\Vue360\Vue360ApiService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ZoneController extends Controller
{
    public function __construct(
        private readonly Vue360ApiService $api
    ) {}

    public function index(Request $request): JsonResponse
    {
        return response()->json(['data' => $this->api->zonesForUser($request->user())]);
    }

    public function show(Request $request, string $id): JsonResponse
    {
        $zone = $this->api->zoneForUser($request->user(), $id);

        if (!$zone) {
            return response()->json(['message' => 'Zone introuvable'], 404);
        }

        return response()->json(['data' => $zone]);
    }
}
