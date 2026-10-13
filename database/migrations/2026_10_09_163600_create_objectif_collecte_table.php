<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Photo mensuelle des objectifs collecte épargne à vue.
     */
    public function up(): void
    {
        if (! Schema::hasTable('objectif_collecte')) {
            Schema::create('objectif_collecte', function (Blueprint $table) {
                $table->id();
                $table->string('month_key')->index();
                $table->string('code_agence')->nullable();
                $table->string('branch_name')->nullable();
                $table->string('code_caf')->nullable();
                $table->string('charge_affaire')->nullable();
                $table->string('matricule_client')->nullable();
                $table->string('numero_compte')->nullable();
                $table->string('nom_client')->nullable();
                $table->double('cum_montant_finance')->nullable();
                $table->double('cum_encours_credit')->nullable();
                $table->double('obj_col_epv_vue')->nullable();
                $table->index(['month_key', 'code_agence', 'code_caf', 'matricule_client', 'numero_compte'], 'idx_objectif_collecte_key');
            });
        }

        if (! Schema::hasTable('objectif_collecte_meta')) {
            Schema::create('objectif_collecte_meta', function (Blueprint $table) {
                $table->string('month_key')->primary();
                $table->text('refreshed_at')->nullable();
                $table->integer('row_count')->nullable();
                $table->string('status')->nullable();
                $table->text('error_message')->nullable();
                $table->float('elapsed_seconds')->nullable();
            });
        }
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('objectif_collecte');
        Schema::dropIfExists('objectif_collecte_meta');
    }
};
