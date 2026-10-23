<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('promesses', function (Blueprint $table) {
            $table->id();
            $table->string('no_pret', 64)->index();
            $table->string('matricule_client', 64)->nullable();
            $table->string('nom_client')->nullable();
            $table->string('code_agence', 16)->nullable();
            $table->string('nom_agence')->nullable();
            $table->string('charge_affaire')->nullable();
            $table->string('compte', 64)->nullable();
            $table->string('type_echange', 16);
            $table->date('date_echange');
            $table->decimal('montant_exigible', 18, 2)->default(0);
            $table->decimal('montant_promis', 18, 2);
            $table->date('date_paiement');
            $table->date('date_relance')->nullable();
            $table->text('commentaire')->nullable();
            $table->string('statut', 16)->default('attente');
            $table->text('motif_annulation')->nullable();
            $table->foreignId('promesse_origine_id')->nullable()->constrained('promesses')->nullOnDelete();
            $table->foreignId('user_id')->nullable()->constrained('users')->nullOnDelete();
            $table->timestamps();
        });

        Schema::create('echanges_clients', function (Blueprint $table) {
            $table->id();
            $table->string('no_pret', 64)->index();
            $table->string('matricule_client', 64)->nullable();
            $table->string('nom_client')->nullable();
            $table->string('type_echange', 16);
            $table->date('date_echange');
            $table->string('resultat')->nullable();
            $table->string('prochaine_action')->nullable();
            $table->text('commentaire')->nullable();
            $table->decimal('montant_promis', 18, 2)->nullable();
            $table->date('date_paiement')->nullable();
            $table->foreignId('promesse_id')->nullable()->constrained('promesses')->nullOnDelete();
            $table->foreignId('user_id')->nullable()->constrained('users')->nullOnDelete();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('echanges_clients');
        Schema::dropIfExists('promesses');
    }
};
