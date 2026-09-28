<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('environments', function (Blueprint $table) {
            $table->id();
            $table->string('name')->unique();
            $table->timestamps();
        });

        $now = now();
        DB::table('environments')->insert([
            ['name' => 'SENEGAL', 'created_at' => $now, 'updated_at' => $now],
            ['name' => 'TOGO', 'created_at' => $now, 'updated_at' => $now],
            ['name' => 'GABON', 'created_at' => $now, 'updated_at' => $now],
            ['name' => 'CONGO', 'created_at' => $now, 'updated_at' => $now],
        ]);

        Schema::table('agencies', function (Blueprint $table) {
            $table->foreignId('environment_id')
                ->nullable()
                ->after('territory_id')
                ->constrained('environments')
                ->nullOnDelete();
        });

        $senegalId = DB::table('environments')->where('name', 'SENEGAL')->value('id');
        if ($senegalId) {
            DB::table('agencies')->whereNull('environment_id')->update([
                'environment_id' => $senegalId,
            ]);
        }
    }

    public function down(): void
    {
        Schema::table('agencies', function (Blueprint $table) {
            $table->dropConstrainedForeignId('environment_id');
        });

        Schema::dropIfExists('environments');
    }
};
