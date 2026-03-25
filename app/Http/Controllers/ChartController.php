<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

class ChartController extends Controller
{
    /**
     * URL de base du service Python
     */
    private $pythonServiceUrl;

    public function __construct()
    {
        // Récupérer l'URL du service Python depuis la config ou .env
        $this->pythonServiceUrl = env('PYTHON_SERVICE_URL', 'http://localhost:8001');
    }

    /**
     * Client HTTP vers le service Python : aucune limite de durée (timeout / connect_timeout = 0).
     */
    private function pythonHttp()
    {
        return Http::timeout(0)->connectTimeout(0);
    }

    /**
     * Génère un graphique en ligne (time series)
     */
    public function timeseries(Request $request): JsonResponse
    {
        try {
            $response = $this->pythonHttp()->post("{$this->pythonServiceUrl}/api/charts/timeseries", [
                'labels' => $request->input('labels', []),
                'values' => $request->input('values', []),
                'title' => $request->input('title', 'Évolution des données'),
                'ylabel' => $request->input('ylabel', 'Valeur'),
            ]);

            if ($response->successful()) {
                return response()->json($response->json());
            }

            return response()->json([
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ], 500);

        } catch (\Exception $e) {
            Log::error('Erreur lors de la génération du graphique time series: ' . $e->getMessage());
            return response()->json([
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Génère un graphique multi-séries
     */
    public function multiseries(Request $request): JsonResponse
    {
        try {
            $response = $this->pythonHttp()->post("{$this->pythonServiceUrl}/api/charts/multiseries", [
                'labels' => $request->input('labels', []),
                'series' => $request->input('series', []),
                'title' => $request->input('title', 'Graphique multi-séries'),
                'ylabel' => $request->input('ylabel', 'Valeur'),
            ]);

            if ($response->successful()) {
                return response()->json($response->json());
            }

            return response()->json([
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ], 500);

        } catch (\Exception $e) {
            Log::error('Erreur lors de la génération du graphique multi-séries: ' . $e->getMessage());
            return response()->json([
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Génère un graphique en barres
     */
    public function barchart(Request $request): JsonResponse
    {
        try {
            $response = $this->pythonHttp()->post("{$this->pythonServiceUrl}/api/charts/barchart", [
                'labels' => $request->input('labels', []),
                'values' => $request->input('values', []),
                'title' => $request->input('title', 'Graphique en barres'),
                'xlabel' => $request->input('xlabel', 'Catégorie'),
                'ylabel' => $request->input('ylabel', 'Valeur'),
                'colors' => $request->input('colors'),
            ]);

            if ($response->successful()) {
                return response()->json($response->json());
            }

            return response()->json([
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ], 500);

        } catch (\Exception $e) {
            Log::error('Erreur lors de la génération du graphique en barres: ' . $e->getMessage());
            return response()->json([
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Génère un graphique d'évolution comparant période actuelle et précédente
     */
    public function evolution(Request $request): JsonResponse
    {
        try {
            $response = $this->pythonHttp()->post("{$this->pythonServiceUrl}/api/charts/evolution", [
                'labels' => $request->input('labels', []),
                'current' => $request->input('current', []),
                'previous' => $request->input('previous'),
                'title' => $request->input('title', 'Évolution temporelle'),
                'ylabel' => $request->input('ylabel', 'Valeur'),
            ]);

            if ($response->successful()) {
                return response()->json($response->json());
            }

            return response()->json([
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ], 500);

        } catch (\Exception $e) {
            Log::error('Erreur lors de la génération du graphique d\'évolution: ' . $e->getMessage());
            return response()->json([
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ], 500);
        }
    }

    /**
     * Génère un graphique circulaire (camembert)
     */
    public function pie(Request $request): JsonResponse
    {
        try {
            $response = $this->pythonHttp()->post("{$this->pythonServiceUrl}/api/charts/pie", [
                'labels' => $request->input('labels', []),
                'values' => $request->input('values', []),
                'title' => $request->input('title', 'Graphique circulaire'),
                'colors' => $request->input('colors'),
            ]);

            if ($response->successful()) {
                return response()->json($response->json());
            }

            return response()->json([
                'error' => 'Erreur du service Python',
                'message' => $response->body()
            ], 500);

        } catch (\Exception $e) {
            Log::error('Erreur lors de la génération du graphique circulaire: ' . $e->getMessage());
            return response()->json([
                'error' => 'Erreur interne',
                'message' => $e->getMessage()
            ], 500);
        }
    }
}

