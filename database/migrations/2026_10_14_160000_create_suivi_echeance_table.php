<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Sauvegarde journalière du suivi échéance (une photo par jour).
     */
    public function up(): void
    {
        if (! Schema::hasTable('suivi_echeance')) {
            Schema::create('suivi_echeance', function (Blueprint $table) {
                $table->id();
                $table->text('jour')->index();
                $table->unsignedSmallInteger('annee');
                $table->unsignedTinyInteger('mois');
                foreach ($this->columns() as $column) {
                    $table->text($column)->nullable();
                }
                $table->index(['annee', 'mois', 'jour']);
                $table->index(['jour', 'no_pret']);
                $table->index(['jour', 'code_agence']);
            });
        }

        if (! Schema::hasTable('suivi_echeance_meta')) {
            Schema::create('suivi_echeance_meta', function (Blueprint $table) {
                $table->text('jour')->primary();
                $table->unsignedSmallInteger('annee')->nullable();
                $table->unsignedTinyInteger('mois')->nullable();
                $table->text('date_debut')->nullable();
                $table->text('date_fin')->nullable();
                $table->text('refreshed_at')->nullable();
                $table->integer('row_count')->nullable();
                $table->string('status')->nullable();
                $table->text('error_message')->nullable();
                $table->float('elapsed_seconds')->nullable();
            });
        }
    }

    public function down(): void
    {
        Schema::dropIfExists('suivi_echeance');
        Schema::dropIfExists('suivi_echeance_meta');
    }

    /**
     * @return list<string>
     */
    private function columns(): array
    {
        return [
            'code_agence',
            'nom_agence',
            'no_pret',
            'matricule_client',
            'nom_client',
            'compte',
            'type_pret',
            'date_deblocage',
            'montant_capital_accorde',
            'encours_total',
            'encours_sain',
            'encours_impaye',
            'pourcentage_remboursement',
            'statut_pret',
            'statut_declassement',
            'code_gestion_pret',
            'charge_affaire',
            'montant_depot_garantie_initial',
            'solde_depot_garantie',
            'schedule_due_date',
            'numero_echeance',
            'solde_cpte',
            'mt_global_due_a_date',
            'etat_exigible_m_1',
            'total_charge',
            'montant_echeance_m',
            'montant_echeance_paye',
            'montant_echeance_impy',
            'penalite',
            'exigible_ech',
            'status_ech',
        ];
    }
};
