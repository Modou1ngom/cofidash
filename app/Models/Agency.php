<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Agency extends Model
{
    use HasFactory;

    protected $fillable = [
        'code',
        'name',
        'description',
        'territory_id',
        'environment_id',
        'chef_agence_user_id',
        'is_active'
    ];

    protected $casts = [
        'is_active' => 'boolean'
    ];

    // Relation avec le territoire
    public function territory()
    {
        return $this->belongsTo(Territory::class);
    }

    public function environment()
    {
        return $this->belongsTo(Environment::class);
    }

    // Relation avec le chef d'agence
    public function chefAgence()
    {
        return $this->belongsTo(User::class, 'chef_agence_user_id');
    }

    // Relation avec les utilisateurs de l'agence
    public function users()
    {
        return $this->hasMany(User::class);
    }
}
