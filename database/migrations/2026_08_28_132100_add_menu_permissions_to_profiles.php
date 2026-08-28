<?php

use App\Models\Profile;
use Illuminate\Database\Migrations\Migration;

return new class extends Migration
{
    public function up(): void
    {
        Profile::query()->each(function (Profile $profile) {
            $permissions = Profile::normalizePermissions($profile->permissions ?? []);
            $menus = Profile::defaultMenuPermissions((string) $profile->code);
            $profile->permissions = array_values(array_unique(array_merge($permissions, $menus)));
            $profile->save();
        });
    }

    public function down(): void
    {
        Profile::query()->each(function (Profile $profile) {
            $permissions = Profile::normalizePermissions($profile->permissions ?? []);
            $profile->permissions = array_values(array_filter(
                $permissions,
                static fn (string $permission) => !str_starts_with($permission, 'MENU_')
            ));
            $profile->save();
        });
    }
};
