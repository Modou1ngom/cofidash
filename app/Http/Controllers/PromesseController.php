<?php

namespace App\Http\Controllers;

use App\Models\EchangeClient;
use App\Models\Promesse;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\DB;
use Illuminate\Validation\Rule;

class PromesseController extends Controller
{
    public function index(): JsonResponse
    {
        $promesses = Promesse::query()
            ->with('user:id,name')
            ->orderByDesc('date_paiement')
            ->orderByDesc('id')
            ->get();

        return response()->json(['promesses' => $promesses]);
    }

    public function store(Request $request): JsonResponse
    {
        $data = $this->validated($request);

        $promesse = DB::transaction(function () use ($data) {
            $promesse = Promesse::create([
                ...$data,
                'statut' => 'attente',
                'user_id' => Auth::id(),
            ]);
            $this->trace($promesse, sprintf('Promesse de %s FCFA', number_format($promesse->montant_promis, 0, ',', ' ')));

            return $promesse;
        });

        return response()->json(['promesse' => $promesse->load('user:id,name')], 201);
    }

    public function reporter(Request $request, int $id): JsonResponse
    {
        $origin = Promesse::findOrFail($id);
        if (in_array($origin->statut, ['annulee', 'reportee'], true)) {
            return response()->json(['message' => 'Cette promesse ne peut plus être reportée.'], 422);
        }

        $data = $request->validate([
            'type_echange' => ['required', Rule::in(['appel', 'visite', 'sms', 'autre'])],
            'date_echange' => ['required', 'date'],
            'montant_promis' => ['required', 'numeric', 'gt:0'],
            'date_paiement' => ['required', 'date'],
            'date_relance' => ['nullable', 'date'],
            'commentaire' => ['nullable', 'string'],
        ]);

        $promesse = DB::transaction(function () use ($origin, $data) {
            $promesse = Promesse::create([
                'no_pret' => $origin->no_pret,
                'matricule_client' => $origin->matricule_client,
                'nom_client' => $origin->nom_client,
                'code_agence' => $origin->code_agence,
                'nom_agence' => $origin->nom_agence,
                'charge_affaire' => $origin->charge_affaire,
                'compte' => $origin->compte,
                'montant_exigible' => $origin->montant_exigible,
                'type_echange' => $data['type_echange'],
                'date_echange' => $data['date_echange'],
                'montant_promis' => $data['montant_promis'],
                'date_paiement' => $data['date_paiement'],
                'date_relance' => $data['date_relance'] ?? null,
                'commentaire' => $data['commentaire'] ?? null,
                'statut' => 'attente',
                'promesse_origine_id' => $origin->id,
                'user_id' => Auth::id(),
            ]);
            $origin->update(['statut' => 'reportee']);
            $this->trace($promesse, 'Promesse reportée');

            return $promesse;
        });

        return response()->json(['promesse' => $promesse->load('user:id,name')], 201);
    }

    public function annuler(Request $request, int $id): JsonResponse
    {
        $promesse = Promesse::findOrFail($id);
        if (in_array($promesse->statut, ['annulee', 'reportee'], true)) {
            return response()->json(['message' => 'Cette promesse ne peut plus être annulée.'], 422);
        }

        $data = $request->validate([
            'motif' => ['required', 'string', 'max:1000'],
        ]);

        DB::transaction(function () use ($promesse, $data) {
            $promesse->update([
                'statut' => 'annulee',
                'motif_annulation' => $data['motif'],
            ]);
            $this->trace($promesse, 'Promesse annulée : '.$data['motif']);
        });

        return response()->json(['promesse' => $promesse->fresh()->load('user:id,name')]);
    }

    public function echanges(int $id): JsonResponse
    {
        $promesse = Promesse::findOrFail($id);
        $echanges = EchangeClient::query()
            ->with('user:id,name')
            ->where('no_pret', $promesse->no_pret)
            ->orderByDesc('date_echange')
            ->orderByDesc('id')
            ->get();

        return response()->json(['echanges' => $echanges]);
    }

    private function validated(Request $request): array
    {
        return $request->validate([
            'no_pret' => ['required', 'string', 'max:64'],
            'matricule_client' => ['nullable', 'string', 'max:64'],
            'nom_client' => ['nullable', 'string', 'max:255'],
            'code_agence' => ['nullable', 'string', 'max:16'],
            'nom_agence' => ['nullable', 'string', 'max:255'],
            'charge_affaire' => ['nullable', 'string', 'max:255'],
            'compte' => ['nullable', 'string', 'max:64'],
            'type_echange' => ['required', Rule::in(['appel', 'visite', 'sms', 'autre'])],
            'date_echange' => ['required', 'date'],
            'montant_exigible' => ['nullable', 'numeric', 'min:0'],
            'montant_promis' => ['required', 'numeric', 'gt:0'],
            'date_paiement' => ['required', 'date'],
            'date_relance' => ['nullable', 'date'],
            'commentaire' => ['nullable', 'string'],
        ]);
    }

    private function trace(Promesse $promesse, string $resultat): void
    {
        $action = $promesse->date_relance
            ? 'Relancer le '.$promesse->date_relance->format('d/m/Y')
            : ($promesse->date_paiement ? 'Vérifier le paiement le '.$promesse->date_paiement->format('d/m/Y') : null);

        EchangeClient::create([
            'no_pret' => $promesse->no_pret,
            'matricule_client' => $promesse->matricule_client,
            'nom_client' => $promesse->nom_client,
            'type_echange' => $promesse->type_echange,
            'date_echange' => $promesse->date_echange,
            'resultat' => $resultat,
            'prochaine_action' => $action,
            'commentaire' => $promesse->commentaire,
            'montant_promis' => $promesse->montant_promis,
            'date_paiement' => $promesse->date_paiement,
            'promesse_id' => $promesse->id,
            'user_id' => Auth::id(),
        ]);
    }
}
