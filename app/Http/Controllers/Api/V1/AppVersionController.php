<?php

namespace App\Http\Controllers\Api\V1;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;

class AppVersionController extends Controller
{
    /**
     * Version minimale / dernière version de l'app mobile (public, avant login).
     */
    public function show(): JsonResponse
    {
        return response()->json([
            'latest_version' => (string) config('mobile_app.latest_version'),
            'min_version' => (string) config('mobile_app.min_version'),
            'force_update' => (bool) config('mobile_app.force_update'),
            'store_url_android' => (string) config('mobile_app.store_url_android'),
            'store_url_ios' => (string) config('mobile_app.store_url_ios'),
            'message' => (string) config('mobile_app.message'),
        ]);
    }
}
