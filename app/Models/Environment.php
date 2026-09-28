<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Environment extends Model
{
    protected $fillable = ['name'];

    public function agencies(): HasMany
    {
        return $this->hasMany(Agency::class);
    }
}
