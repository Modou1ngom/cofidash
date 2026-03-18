<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class ReferenceCompteBloc extends Model
{
    protected $fillable = ['libelle', 'sort_order', 'cle_repartition_nom'];

    protected $casts = [
        'sort_order' => 'integer',
    ];

    public function rubriques(): HasMany
    {
        return $this->hasMany(ReferenceCompteRubrique::class, 'bloc_id')->orderBy('sort_order');
    }
}
