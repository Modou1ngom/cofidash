<?php

use App\Models\Profile;
use Illuminate\Database\Migrations\Migration;

return new class extends Migration
{
    public function up(): void
    {
        Profile::query()->each(function (Profile $profile) {
            $permissions = Profile::normalizePermissions($profile->permissions ?? []);
            if (($profile->code ?? '') === 'CC') {
                return;
            }
            if (!in_array('MENU_PI', $permissions, true)) {
                $permissions[] = 'MENU_PI';
                $profile->permissions = $permissions;
                $profile->save();
            }
        });
    }

    public function down(): void
    {
        Profile::query()->each(function (Profile $profile) {
            $permissions = Profile::normalizePermissions($profile->permissions ?? []);
            $filtered = array_values(array_filter(
                $permissions,
                static fn (string $permission) => $permission !== 'MENU_PI'
            ));
            if ($filtered !== $permissions) {
                $profile->permissions = $filtered;
                $profile->save();
            }
        });
    }
};
