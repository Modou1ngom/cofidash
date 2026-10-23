<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class EchangeClient extends Model
{
    protected $table = 'echanges_clients';

    protected $fillable = [
        'no_pret',
        'matricule_client',
        'nom_client',
        'type_echange',
        'date_echange',
        'resultat',
        'prochaine_action',
        'commentaire',
        'montant_promis',
        'date_paiement',
        'promesse_id',
        'user_id',
    ];

    protected $casts = [
        'date_echange' => 'date',
        'date_paiement' => 'date',
        'montant_promis' => 'float',
    ];

    public function promesse(): BelongsTo
    {
        return $this->belongsTo(Promesse::class);
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
