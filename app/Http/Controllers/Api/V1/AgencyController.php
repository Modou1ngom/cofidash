<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use App\Services\Vue360\Vue360ApiService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class AgencyController extends Controller
{
    public function __construct(
        private readonly Vue360ApiService $api
    ) {}

    public function index(Request $request): JsonResponse
    {
        return response()->json(['data' => $this->api->agenciesForUser($request->user())]);
    }

    public function show(Request $request, string $id): JsonResponse
    {
        $agency = $this->api->agencyForUser($request->user(), $id);

        if (!$agency) {
            return response()->json(['message' => 'Agence introuvable'], 404);
        }

        return response()->json(['data' => $agency]);
    }
}
