<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Sauvegarde du suivi de production (résultat de suivi_production.sql).
     */
    public function up(): void
    {
        if (! Schema::hasTable('suivi_production')) {
            Schema::create('suivi_production', function (Blueprint $table) {
                $table->id();
                $table->unsignedSmallInteger('annee')->index();
                foreach ($this->columns() as $column) {
                    $table->text($column)->nullable();
                }
                $table->index(['annee', 'date_deblocage']);
                $table->index('no_pret');
                $table->index(['annee', 'code_agence']);
            });
        }

        if (! Schema::hasTable('suivi_production_meta')) {
            Schema::create('suivi_production_meta', function (Blueprint $table) {
                $table->unsignedSmallInteger('annee')->primary();
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

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('suivi_production');
        Schema::dropIfExists('suivi_production_meta');
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
            'type_pret_gl',
            'type_pret',
            'date_mise_en_place',
            'date_val_mise_en_place',
            'date_deblocage',
            'date_maturite',
            'date_premiere_echeance',
            'date_derniere_echeance',
            'montant_capital_accorde',
            'statut_pret',
            'periodicite',
            'cpt_depot_garantie',
            'udf_cpt_depot_garantie',
            'montant_depot_garantie_initial',
            'udf_montant_depot_garantie_initial',
            'solde_depot_garantie',
            'frais_dossier',
            'frais_assurance',
            'taux_de_credit',
            'code_gestion_pret',
            'charge_affaire',
            'encours_total',
            'encours_sain',
            'encours_impaye',
            'pourcentage_remboursement',
            'maker_id',
            'account_number',
            'code_type_produit',
            'type_produit',
            'ref_credit_restructure',
            'famille_type_credit',
            'famille_credit',
            'code_sous_famille_credit',
            'sous_famille_credit',
            'code_secteur_activite',
            'secteur_activite',
            'code_sous_secteur',
            'sous_secteur',
            'reference_comite',
            'code_nature_credit',
            'nature_credit',
            'name_numero_de_contrat',
            'id_protocoles',
            'rebooke',
            'code_ref_credit_restructure',
            'no_contrat_restructure',
            'code_bloc',
            'bloc',
            'code_campagne',
            'campagne',
            'code_recouvreur',
            'name_recouvreur',
            'id_ligne_financement',
            'numero_credit_flow',
            'compte_pep',
            'montant_pep',
        ];
    }
};
