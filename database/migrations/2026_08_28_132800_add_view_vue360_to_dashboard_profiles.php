<?php

use App\Models\Profile;
use Illuminate\Database\Migrations\Migration;

return new class extends Migration
{
    public function up(): void
    {
        Profile::query()->each(function (Profile $profile) {
            $permissions = Profile::normalizePermissions($profile->permissions ?? []);
            if (in_array('VIEW_DASHBOARD', $permissions, true) && !in_array('VIEW_VUE360', $permissions, true)) {
                $permissions[] = 'VIEW_VUE360';
                $profile->permissions = $permissions;
                $profile->save();
            }
        });
    }

    public function down(): void
    {
        // Intentionally left empty: VIEW_VUE360 may already have been assigned manually.
    }
};
