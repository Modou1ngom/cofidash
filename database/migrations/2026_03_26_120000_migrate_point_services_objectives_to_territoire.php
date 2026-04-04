<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Remplace la catégorie historique « POINT SERVICES » par « TERRITOIRE »
     * (même périmètre métier après fusion des points de service dans Dakar Ville).
     */
    public function up(): void
    {
        if (! Schema::hasTable('objectives')) {
            return;
        }

        if (! Schema::hasColumn('objectives', 'category')) {
            return;
        }

        DB::table('objectives')
            ->where('category', 'POINT SERVICES')
            ->update(['category' => 'TERRITOIRE']);
    }

    /**
     * Réversion non fiable : on ne peut pas distinguer les lignes migrées
     * des objectifs « TERRITOIRE » créés après cette migration.
     */
    public function down(): void
    {
        //
    }
};
