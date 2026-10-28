<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('promesses', function (Blueprint $table) {
            $table->decimal('montant_deja_paye', 18, 2)->default(0);
        });

        if (Schema::hasTable('suivi_echeance')) {
            DB::statement("
                UPDATE promesses
                SET montant_deja_paye = (
                    SELECT COALESCE(SUM(CAST(montant_echeance_paye AS REAL)), 0)
                    FROM suivi_echeance
                    WHERE suivi_echeance.no_pret = promesses.no_pret
                )
            ");
        }
    }

    public function down(): void
    {
        Schema::table('promesses', function (Blueprint $table) {
            $table->dropColumn('montant_deja_paye');
        });
    }
};
