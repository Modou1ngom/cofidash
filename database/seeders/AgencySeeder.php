<?php

namespace Database\Seeders;

use App\Models\Agency;
use App\Models\Territory;
use App\Models\User;
use Illuminate\Database\Seeder;

class AgencySeeder extends Seeder
{
    /**
     * Par défaut aucune agence en seed : les codes officiels sont CODE_BUREAU / DASH_RELATION (Oracle),
     * synchronisés avec agencies:sync-from-oracle.
     *
     * Pour remplir config/cofi_agencies.php en dev uniquement (tableau de ['code','name','territory_code']).
     */
    public function run(): void
    {
        $rows = config('cofi_agencies', []);
        if ($rows === [] || $rows === null) {
            return;
        }

        foreach ($rows as $territoryCode => $items) {
            $territory = Territory::where('code', $territoryCode)->first();
            if (! $territory || ! is_array($items)) {
                continue;
            }
            foreach ($items as $item) {
                if (! is_array($item) || empty($item['code']) || empty($item['name'])) {
                    continue;
                }
                Agency::updateOrCreate(
                    ['code' => strtoupper(trim((string) $item['code']))],
                    [
                        'name' => trim((string) $item['name']),
                        'territory_id' => $territory->id,
                        'is_active' => true,
                    ]
                );
            }
        }
    }
}
