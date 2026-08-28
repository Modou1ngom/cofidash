<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable;

    protected $fillable = [
        'name',
        'email',
        'password',
        'must_change_password',
        'profile_photo_path',
        'profile_id',
        'territory_id',
        'agency_id',
        'manager_code',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    protected $casts = [
        'email_verified_at' => 'datetime',
        'password' => 'hashed',
        'must_change_password' => 'boolean',
    ];

    public function profile()
    {
        return $this->belongsTo(Profile::class);
    }

    public function hasPermission(string $permission): bool
    {
        if (!$this->profile || !$this->profile->is_active) {
            return false;
        }

        $permissions = Profile::normalizePermissions($this->profile->permissions ?? []);
        $wanted = Profile::normalizePermissions([$permission])[0] ?? strtoupper($permission);
        return in_array($wanted, $permissions, true);
    }

    // Relation avec le territoire
    public function territory()
    {
        return $this->belongsTo(Territory::class);
    }

    // Relation avec l'agence
    public function agency()
    {
        return $this->belongsTo(Agency::class);
    }

    // Territoire dont l'utilisateur est responsable
    public function responsibleTerritory()
    {
        return $this->hasOne(Territory::class, 'responsible_user_id');
    }

    // Agence dont l'utilisateur est chef
    public function managedAgency()
    {
        return $this->hasOne(Agency::class, 'chef_agence_user_id');
    }
}

