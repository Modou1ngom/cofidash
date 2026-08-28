<?php

use App\Models\Profile;
use Illuminate\Database\Migrations\Migration;

return new class extends Migration
{
    public function up(): void
    {
        Profile::query()->each(function (Profile $profile) {
            $permissions = Profile::normalizePermissions($profile->permissions ?? []);

            if (strtoupper((string) $profile->code) === 'CAF') {
                $permissions = Profile::CAF_PERMISSIONS;
            }

            $profile->permissions = $permissions;
            $profile->save();
        });
    }

    public function down(): void
    {
        // Irreversible normalisation of permission keys.
    }
};
