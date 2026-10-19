<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Objectif de recouvrement figé le 1er de chaque mois.
     */
    public function up(): void
    {
        if (! Schema::hasTable('objectif_recouvrement')) {
            Schema::create('objectif_recouvrement', function (Blueprint $table) {
                $table->id();
                $table->unsignedSmallInteger('annee');
                $table->unsignedTinyInteger('mois');
                $table->text('account_number')->nullable();
                $table->text('statut_pret')->nullable();
                $table->text('exigible_m_1')->nullable();
                $table->text('montant_echeance')->nullable();
                $table->text('objectif_recouvrement')->nullable();
                $table->index(['annee', 'mois']);
                $table->index(['annee', 'mois', 'account_number']);
            });
        }

        if (! Schema::hasTable('objectif_recouvrement_meta')) {
            Schema::create('objectif_recouvrement_meta', function (Blueprint $table) {
                $table->unsignedSmallInteger('annee');
                $table->unsignedTinyInteger('mois');
                $table->text('date_debut')->nullable();
                $table->text('date_fin')->nullable();
                $table->text('refreshed_at')->nullable();
                $table->integer('row_count')->nullable();
                $table->string('status')->nullable();
                $table->text('error_message')->nullable();
                $table->float('elapsed_seconds')->nullable();
                $table->primary(['annee', 'mois']);
            });
        }
    }

    public function down(): void
    {
        Schema::dropIfExists('objectif_recouvrement');
        Schema::dropIfExists('objectif_recouvrement_meta');
    }
};
