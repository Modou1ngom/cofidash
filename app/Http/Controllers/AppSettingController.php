<?php

namespace App\Http\Controllers;

use App\Models\AppSetting;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Validator;

class AppSettingController extends Controller
{
    private const SEUILS_KEY = 'comptes-ouverts-seuils';

    private const DEFAULT_SEUILS = [
        'reached' => 100,
        'close' => 90,
        'vigilance' => 70,
    ];

    public function show(string $key): JsonResponse
    {
        if ($key !== self::SEUILS_KEY) {
            return response()->json(['success' => false, 'message' => 'Paramètre inconnu'], 404);
        }

        $setting = AppSetting::query()->where('key', $key)->first();

        return response()->json([
            'success' => true,
            'data' => $this->normalizeSeuils($setting?->value),
        ]);
    }

    public function upsert(Request $request, string $key): JsonResponse
    {
        if ($key !== self::SEUILS_KEY) {
            return response()->json(['success' => false, 'message' => 'Paramètre inconnu'], 404);
        }

        $user = Auth::user();
        $profile = strtoupper((string) ($user?->profile?->code ?? ''));
        if (! in_array($profile, ['DGA', 'ADMIN'], true)) {
            return response()->json([
                'success' => false,
                'message' => 'Seuls le DGA et l’administrateur peuvent modifier les seuils TRO.',
            ], 403);
        }

        $validator = Validator::make($request->all(), [
            'reached' => 'required|numeric|min:1|max:200',
            'close' => 'required|numeric|min:1|max:200',
            'vigilance' => 'required|numeric|min:1|max:200',
        ]);

        if ($validator->fails()) {
            return response()->json([
                'success' => false,
                'message' => 'Seuils invalides',
                'errors' => $validator->errors(),
            ], 422);
        }

        $data = $validator->validated();
        if (! ($data['reached'] > $data['close'] && $data['close'] > $data['vigilance'])) {
            return response()->json([
                'success' => false,
                'message' => 'Les seuils doivent être décroissants : atteint > proche > vigilance.',
            ], 422);
        }

        $setting = AppSetting::query()->updateOrCreate(
            ['key' => $key],
            [
                'value' => [
                    'reached' => (float) $data['reached'],
                    'close' => (float) $data['close'],
                    'vigilance' => (float) $data['vigilance'],
                ],
                'updated_by' => $user?->id,
            ]
        );

        return response()->json([
            'success' => true,
            'message' => 'Seuils enregistrés.',
            'data' => $this->normalizeSeuils($setting->value),
        ]);
    }

    private function normalizeSeuils(?array $value): array
    {
        $reached = (float) ($value['reached'] ?? self::DEFAULT_SEUILS['reached']);
        $close = (float) ($value['close'] ?? self::DEFAULT_SEUILS['close']);
        $vigilance = (float) ($value['vigilance'] ?? self::DEFAULT_SEUILS['vigilance']);

        if (! ($reached > $close && $close > $vigilance)) {
            return self::DEFAULT_SEUILS;
        }

        return compact('reached', 'close', 'vigilance');
    }
}
