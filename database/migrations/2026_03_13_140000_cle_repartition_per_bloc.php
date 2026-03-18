<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('reference_compte_blocs', function (Blueprint $table) {
            $table->string('cle_repartition_nom', 255)->nullable()->after('sort_order');
        });

        Schema::dropIfExists('reference_compte_cle_repartition');

        Schema::create('reference_compte_cle_repartition', function (Blueprint $table) {
            $table->foreignId('bloc_id')->constrained('reference_compte_blocs')->cascadeOnDelete();
            $table->string('entity_key', 64);
            $table->decimal('value', 15, 4)->default(0);
            $table->timestamps();
            $table->primary(['bloc_id', 'entity_key']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('reference_compte_cle_repartition');
        Schema::table('reference_compte_blocs', function (Blueprint $table) {
            $table->dropColumn('cle_repartition_nom');
        });
        Schema::create('reference_compte_cle_repartition', function (Blueprint $table) {
            $table->string('entity_key', 64)->primary();
            $table->decimal('value', 15, 4)->default(0);
            $table->timestamps();
        });
    }
};
