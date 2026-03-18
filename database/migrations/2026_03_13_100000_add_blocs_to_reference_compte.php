<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('reference_compte_blocs', function (Blueprint $table) {
            $table->id();
            $table->string('libelle');
            $table->unsignedSmallInteger('sort_order')->default(0);
            $table->timestamps();
        });

        Schema::table('reference_compte_rubriques', function (Blueprint $table) {
            $table->foreignId('bloc_id')->nullable()->after('id')->constrained('reference_compte_blocs')->nullOnDelete();
        });

        // Affecter les rubriques existantes à un bloc par défaut
        $count = DB::table('reference_compte_rubriques')->count();
        if ($count > 0) {
            $blocId = DB::table('reference_compte_blocs')->insertGetId([
                'libelle' => 'Par défaut',
                'sort_order' => 0,
                'created_at' => now(),
                'updated_at' => now(),
            ]);
            DB::table('reference_compte_rubriques')->update(['bloc_id' => $blocId]);
        }
    }

    public function down(): void
    {
        Schema::table('reference_compte_rubriques', function (Blueprint $table) {
            $table->dropForeign(['bloc_id']);
        });
        Schema::dropIfExists('reference_compte_blocs');
    }
};
