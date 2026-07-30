<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    private const TYPES_WITH_NEW_DEAL = "ENUM('CLIENT', 'PRODUCTION', 'PRODUCTION_VOLUME', 'ENCOURS_CREDIT', 'COLLECT', 'PRODUCTION_ENCOURS', 'ENCOURS_EPARGNE_SIMPLE', 'ENCOURS_COMPTE', 'ENCOURS_EPARGNE_PROJET', 'ENCOURS_COMPTE_COURANT', 'ENCOURS_EPARGNE_PEP_SIMPLE', 'DEPOT_GARANTIE', 'EPARGNE', 'VIREMENT', 'EPARGNE_SIMPLE', 'EPARGNE_PROJET', 'VOLUME_DAT', 'NEW_DEAL')";

    private const TYPES_WITHOUT_NEW_DEAL = "ENUM('CLIENT', 'PRODUCTION', 'PRODUCTION_VOLUME', 'ENCOURS_CREDIT', 'COLLECT', 'PRODUCTION_ENCOURS', 'ENCOURS_EPARGNE_SIMPLE', 'ENCOURS_COMPTE', 'ENCOURS_EPARGNE_PROJET', 'ENCOURS_COMPTE_COURANT', 'ENCOURS_EPARGNE_PEP_SIMPLE', 'DEPOT_GARANTIE', 'EPARGNE', 'VIREMENT', 'EPARGNE_SIMPLE', 'EPARGNE_PROJET', 'VOLUME_DAT')";

    private const SQLITE_TYPES_WITH = "'CLIENT', 'PRODUCTION', 'PRODUCTION_VOLUME', 'ENCOURS_CREDIT', 'COLLECT', 'PRODUCTION_ENCOURS', 'ENCOURS_EPARGNE_SIMPLE', 'ENCOURS_COMPTE', 'ENCOURS_EPARGNE_PROJET', 'ENCOURS_COMPTE_COURANT', 'ENCOURS_EPARGNE_PEP_SIMPLE', 'DEPOT_GARANTIE', 'EPARGNE', 'VIREMENT', 'EPARGNE_SIMPLE', 'EPARGNE_PROJET', 'VOLUME_DAT', 'NEW_DEAL'";

    private const SQLITE_TYPES_WITHOUT = "'CLIENT', 'PRODUCTION', 'PRODUCTION_VOLUME', 'ENCOURS_CREDIT', 'COLLECT', 'PRODUCTION_ENCOURS', 'ENCOURS_EPARGNE_SIMPLE', 'ENCOURS_COMPTE', 'ENCOURS_EPARGNE_PROJET', 'ENCOURS_COMPTE_COURANT', 'ENCOURS_EPARGNE_PEP_SIMPLE', 'DEPOT_GARANTIE', 'EPARGNE', 'VIREMENT', 'EPARGNE_SIMPLE', 'EPARGNE_PROJET', 'VOLUME_DAT'";

    public function up(): void
    {
        $driver = DB::connection()->getDriverName();

        if ($driver === 'sqlite') {
            $this->recreateSqliteTable(self::SQLITE_TYPES_WITH, includeNewDeal: true);
        } elseif ($driver === 'mysql' || $driver === 'mariadb') {
            DB::statement('ALTER TABLE objectives MODIFY COLUMN type '.self::TYPES_WITH_NEW_DEAL.' NOT NULL');
        } elseif ($driver === 'pgsql') {
            DB::statement("ALTER TYPE objectives_type_enum ADD VALUE IF NOT EXISTS 'NEW_DEAL'");
        }
    }

    public function down(): void
    {
        $driver = DB::connection()->getDriverName();

        if ($driver === 'sqlite') {
            $this->recreateSqliteTable(self::SQLITE_TYPES_WITHOUT, includeNewDeal: false);
        } elseif ($driver === 'mysql' || $driver === 'mariadb') {
            DB::table('objectives')->where('type', 'NEW_DEAL')->delete();
            DB::statement('ALTER TABLE objectives MODIFY COLUMN type '.self::TYPES_WITHOUT_NEW_DEAL.' NOT NULL');
        }
    }

    private function recreateSqliteTable(string $typesList, bool $includeNewDeal): void
    {
        DB::statement('DROP TABLE IF EXISTS objectives_new');
        DB::statement("
            CREATE TABLE objectives_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ({$typesList})),
                category TEXT NOT NULL CHECK(category IN ('FILIALE', 'TERRITOIRE', 'POINT SERVICES', 'GRAND COMPTE')),
                territory TEXT,
                agency_code TEXT NOT NULL DEFAULT '',
                agency_name TEXT,
                value INTEGER NOT NULL,
                value_nombres INTEGER,
                value_volume INTEGER,
                period TEXT NOT NULL CHECK(period IN ('month', 'quarter', 'year')),
                year INTEGER NOT NULL,
                month INTEGER,
                quarter INTEGER,
                description TEXT,
                status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'pending_validation', 'validated', 'rejected')),
                created_by INTEGER,
                validated_by INTEGER,
                validated_at TIMESTAMP,
                rejection_reason TEXT,
                zone TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ");

        $where = $includeNewDeal ? '' : " WHERE type != 'NEW_DEAL'";
        DB::statement("
            INSERT INTO objectives_new
            (id, type, category, territory, agency_code, agency_name, value, value_nombres, value_volume, period, year, month, quarter, description, status, created_by, validated_by, validated_at, rejection_reason, zone, created_at, updated_at)
            SELECT
            id, type, category, territory, agency_code, agency_name, value, value_nombres, value_volume, period, year, month, quarter, description, status, created_by, validated_by, validated_at, rejection_reason, zone, created_at, updated_at
            FROM objectives{$where}
        ");

        Schema::dropIfExists('objectives');
        DB::statement('ALTER TABLE objectives_new RENAME TO objectives');
        DB::statement('CREATE INDEX idx_objectives_type_category ON objectives(type, category, agency_code, year, month)');
        DB::statement('CREATE INDEX idx_objectives_agency_year_month ON objectives(agency_code, year, month)');
    }
};
