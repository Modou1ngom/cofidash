<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('reference_compte_cle_repartition', function (Blueprint $table) {
            $table->string('entity_key', 64)->primary();
            $table->decimal('value', 15, 4)->default(0);
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('reference_compte_cle_repartition');
    }
};
