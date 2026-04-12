<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $this->call([
            ProfileSeeder::class,
            TerritorySeeder::class,
            AgencySeeder::class,
            UserSeeder::class,
            ReferenceCompteSeeder::class,
        ]);
    }
}

