<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\ProfileController;
use App\Http\Controllers\ChartController;
use App\Http\Controllers\DataController;
use App\Http\Controllers\ObjectiveController;
use App\Http\Controllers\ReferenceCompteController;
use App\Http\Controllers\TerritoryController;
use App\Http\Controllers\AgencyController;

// Routes publiques
Route::post('/login', [AuthController::class, 'login']);
Route::get('/profiles', [AuthController::class, 'getProfiles']);

// Routes pour les graphiques Python
Route::prefix('charts')->group(function () {
    Route::post('/timeseries', [ChartController::class, 'timeseries']);
    Route::post('/multiseries', [ChartController::class, 'multiseries']);
    Route::post('/barchart', [ChartController::class, 'barchart']);
    Route::post('/evolution', [ChartController::class, 'evolution']);
    Route::post('/pie', [ChartController::class, 'pie']);
});

// Routes pour les données Oracle
Route::prefix('oracle')->group(function () {
    Route::get('/test', [DataController::class, 'testOracleConnection']);
    Route::get('/tables', [DataController::class, 'getTables']);
    Route::post('/query', [DataController::class, 'executeQuery']);
    Route::get('/table/{tableName}', [DataController::class, 'getTableData']);
    Route::get('/data/clients', [DataController::class, 'getClientsData']);
    Route::get('/data/agencies-from-dash', [DataController::class, 'getAgenciesFromDashData']);
    Route::get('/data/production', [DataController::class, 'getProductionData']);
    Route::get('/data/production-volume', [DataController::class, 'getProductionVolumeData']);
    Route::get('/data/encours-credit', [DataController::class, 'getEncoursCreditData']);
    Route::get('/data/encours', [DataController::class, 'getEncoursData']);
    Route::get('/data/collection', [DataController::class, 'getCollectionData']);
    Route::get('/data/volume-dat', [DataController::class, 'getVolumeDatData']);
    Route::get('/data/depot-garantie', [DataController::class, 'getDepotGarantieData']);
    Route::get('/data/domiciliation-flux', [DataController::class, 'getDomiciliationFluxData']);
    Route::get('/data/transfers', [DataController::class, 'getTransfersData']);
    Route::get('/data/prepaid-card-sales', [DataController::class, 'getPrepaidCardSalesData']);
    Route::get('/data/portefeuille-risque', [DataController::class, 'getPortefeuilleRisqueData']);
    Route::get('/data/portefeuille-risque-caf', [DataController::class, 'getPortefeuilleRisqueCafData']);
    Route::get('/data/entrees-par', [DataController::class, 'getEntreesParData']);
    Route::get('/data/stock-provision', [DataController::class, 'getStockProvisionData']);
    Route::get('/data/gl-lookup', [DataController::class, 'getGlLookup']);
    Route::post('/data/cr-par-agence', [DataController::class, 'getCrParAgenceData']);
});

// Référence compte (Reporting Financier)
Route::get('/reference-compte', [ReferenceCompteController::class, 'index']);
Route::post('/reference-compte', [ReferenceCompteController::class, 'store']);

// Routes pour les objectifs (protégées)
Route::middleware('auth:sanctum')->prefix('objectives')->group(function () {
    Route::get('/', [ObjectiveController::class, 'index']);
    Route::get('/pending-validation', [ObjectiveController::class, 'pendingValidation']);
    Route::get('/md-filiale-objective', [ObjectiveController::class, 'getMDFilialeObjective']);
    Route::get('/dga-objective', [ObjectiveController::class, 'getDGAObjective']);
    Route::get('/agency-objectives', [ObjectiveController::class, 'getAgencyObjectives']);
    Route::get('/agency-objectives-sum', [ObjectiveController::class, 'getAgencyObjectivesSum']);
    Route::post('/', [ObjectiveController::class, 'store']);
    Route::put('/{id}', [ObjectiveController::class, 'update']);
    Route::post('/{id}/validate', [ObjectiveController::class, 'validateObjective']);
    Route::post('/{id}/reject', [ObjectiveController::class, 'reject']);
    Route::delete('/{id}', [ObjectiveController::class, 'destroy']);
    Route::get('/test-merge', [ObjectiveController::class, 'testMerge']);
    Route::get('/debug-agencies', [ObjectiveController::class, 'debugAgencies']);
});

// Routes protégées
Route::middleware('auth:sanctum')->group(function () {
    Route::get('/user', [AuthController::class, 'me']);
    Route::post('/logout', [AuthController::class, 'logout']);

    // Alias pratiques pour la gestion territoires / agences (TerritoryAgencyManagement.vue)
    Route::get('/users', [\App\Http\Controllers\UserController::class, 'index']);

    Route::post('/agencies/sync-from-oracle', [AgencyController::class, 'syncFromOracle']);
    Route::post('/agencies/{id}/assign-chef-agence', [AgencyController::class, 'assignChefAgence']);
    Route::apiResource('agencies', AgencyController::class);

    Route::post('/territories/{id}/assign-responsible', [TerritoryController::class, 'assignResponsible']);
    Route::apiResource('territories', TerritoryController::class);
    
    // Routes admin
    Route::prefix('admin')->group(function () {
        Route::apiResource('profiles', ProfileController::class);
        Route::apiResource('users', \App\Http\Controllers\UserController::class);
    });
});

