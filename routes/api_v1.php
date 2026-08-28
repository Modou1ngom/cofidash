<?php

use App\Http\Controllers\Api\V1\AgencyController;
use App\Http\Controllers\Api\V1\AppVersionController;
use App\Http\Controllers\Api\V1\AuthController;
use App\Http\Controllers\Api\V1\ClientController;
use App\Http\Controllers\Api\V1\CreditController;
use App\Http\Controllers\Api\V1\DashboardController;
use App\Http\Controllers\Api\V1\DatDepositController;
use App\Http\Controllers\Api\V1\NotificationController;
use App\Http\Controllers\Api\V1\OpportunityController;
use App\Http\Controllers\Api\V1\RiskController;
use App\Http\Controllers\Api\V1\ZoneController;
use Illuminate\Support\Facades\Route;

/*
| COFINA CLIENT VUE 360 — API v1 (Flutter mobile)
| Préfixe final : /api/v1
*/

// Public — contrôle de version au démarrage (avant login)
Route::get('/app/version', [AppVersionController::class, 'show']);

Route::prefix('auth')->group(function () {
    Route::post('/login', [AuthController::class, 'login']);
    Route::middleware('auth:sanctum')->group(function () {
        Route::get('/me', [AuthController::class, 'me']);
        Route::post('/logout', [AuthController::class, 'logout']);
        Route::post('/profile-photo', [AuthController::class, 'uploadProfilePhoto']);
        Route::delete('/profile-photo', [AuthController::class, 'deleteProfilePhoto']);
        Route::get('/caf-managers', [AuthController::class, 'cafManagers']);
        Route::post('/manager-code', [AuthController::class, 'setManagerCode']);
        Route::post('/change-password', [AuthController::class, 'changePassword']);
    });
});

Route::middleware('auth:sanctum')->group(function () {
    Route::get('/clients', [ClientController::class, 'index']);
    Route::get('/clients/{id}', [ClientController::class, 'show']);
    Route::get('/clients/{id}/accounts', [ClientController::class, 'accounts']);
    Route::get('/clients/{id}/accounts/{accountNo}', [ClientController::class, 'account']);
    Route::get('/clients/{id}/kyc', [ClientController::class, 'kyc']);
    Route::get('/clients/{id}/checking-pi', [ClientController::class, 'checkingPi']);

    Route::get('/credits', [CreditController::class, 'index']);
    Route::get('/credits/{id}/ta', [CreditController::class, 'amortizationSchedule']);
    Route::get('/credits/{id}/repayments', [CreditController::class, 'repayments']);
    Route::get('/credits/{id}', [CreditController::class, 'show']);

    Route::get('/dashboard/kpis', [DashboardController::class, 'kpis']);
    Route::get('/dashboard/caf-overview', [DashboardController::class, 'cafOverview']);
    Route::get('/dashboard/caf-managers', [DashboardController::class, 'cafManagers']);

    Route::get('/agencies', [AgencyController::class, 'index']);
    Route::get('/agencies/{id}', [AgencyController::class, 'show']);

    Route::get('/zones', [ZoneController::class, 'index']);
    Route::get('/zones/{id}', [ZoneController::class, 'show']);

    Route::get('/risks', [RiskController::class, 'index']);
    Route::get('/opportunities', [OpportunityController::class, 'index']);
    Route::get('/notifications', [NotificationController::class, 'index']);
    Route::get('/dat-deposits', [DatDepositController::class, 'index']);
});
