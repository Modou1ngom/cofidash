<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::create('reference_compte_rubriques', function (Blueprint $table) {
            $table->id();
            $table->string('libelle');
            $table->unsignedSmallInteger('sort_order')->default(0);
            $table->timestamps();
        });

        Schema::create('reference_compte_gls', function (Blueprint $table) {
            $table->id();
            $table->foreignId('rubrique_id')->constrained('reference_compte_rubriques')->onDelete('cascade');
            $table->string('numero_gl', 50);
            $table->string('nom_gl')->nullable();
            $table->unsignedSmallInteger('sort_order')->default(0);
            $table->timestamps();

            $table->index('rubrique_id');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('reference_compte_gls');
        Schema::dropIfExists('reference_compte_rubriques');
    }
};
