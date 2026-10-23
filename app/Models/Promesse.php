<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Promesse extends Model
{
    protected $fillable = [
        'no_pret',
        'matricule_client',
        'nom_client',
        'code_agence',
        'nom_agence',
        'charge_affaire',
        'compte',
        'type_echange',
        'date_echange',
        'montant_exigible',
        'montant_promis',
        'date_paiement',
        'date_relance',
        'commentaire',
        'statut',
        'motif_annulation',
        'promesse_origine_id',
        'user_id',
    ];

    protected $casts = [
        'date_echange' => 'date',
        'date_paiement' => 'date',
        'date_relance' => 'date',
        'montant_exigible' => 'float',
        'montant_promis' => 'float',
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function echanges(): HasMany
    {
        return $this->hasMany(EchangeClient::class);
    }
}
