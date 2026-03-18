<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class ReferenceCompteGl extends Model
{
    protected $fillable = ['rubrique_id', 'numero_gl', 'nom_gl', 'sort_order'];

    protected $casts = [
        'sort_order' => 'integer',
    ];

    public function rubrique(): BelongsTo
    {
        return $this->belongsTo(ReferenceCompteRubrique::class, 'rubrique_id');
    }
}
