<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class ReferenceCompteRubrique extends Model
{
    protected $fillable = ['bloc_id', 'libelle', 'sort_order'];

    protected $casts = [
        'sort_order' => 'integer',
    ];

    public function bloc(): BelongsTo
    {
        return $this->belongsTo(ReferenceCompteBloc::class, 'bloc_id');
    }

    public function gls(): HasMany
    {
        return $this->hasMany(ReferenceCompteGl::class, 'rubrique_id')->orderBy('sort_order');
    }
}
