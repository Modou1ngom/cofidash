<?php

namespace Database\Seeders;

use App\Models\ReferenceCompteBloc;
use App\Models\ReferenceCompteGl;
use App\Models\ReferenceCompteRubrique;
use Illuminate\Database\Seeder;

class ReferenceCompteSeeder extends Seeder
{
    public function run(): void
    {
        $rubriques = [
            ['libelle' => 'PRODUITS D\'INTERÊTS', 'sort_order' => 0],
            ['libelle' => 'CHARGES D\'INTERÊTS', 'sort_order' => 1],
            ['libelle' => 'MARGE NETTE D\'INTERÊTS', 'sort_order' => 2],
            ['libelle' => 'COMMISSIONS NETTES', 'sort_order' => 3],
            ['libelle' => 'PRODUIT NET BANCAIRE', 'sort_order' => 4],
            ['libelle' => 'CHARGES D\'EXPLOITATION', 'sort_order' => 5],
            ['libelle' => 'PRODUITS D\'EXPLOITATION', 'sort_order' => 6],
            ['libelle' => 'PROVISIONS POUR RISQUES & CHARGES', 'sort_order' => 7],
            ['libelle' => 'COÛT NET DU RISQUE', 'sort_order' => 8],
            ['libelle' => 'RESULTAT EXCEPTIONNEL', 'sort_order' => 9],
            ['libelle' => 'RESULTAT AVANT IMPÔT', 'sort_order' => 10],
            ['libelle' => 'Impôt sur le bénéfice (-)', 'sort_order' => 11],
        ];

        $libellesNormaux = array_column($rubriques, 'libelle');
        $blocsASupprimer = ReferenceCompteBloc::whereNotIn('libelle', $libellesNormaux)->get();
        foreach ($blocsASupprimer as $bloc) {
            foreach ($bloc->rubriques as $rubrique) {
                $rubrique->gls()->delete();
            }
            $bloc->rubriques()->delete();
            $bloc->delete();
        }

        foreach ($rubriques as $order => $r) {
            ReferenceCompteBloc::firstOrCreate(
                ['libelle' => $r['libelle']],
                ['sort_order' => $r['sort_order']]
            );
        }

        $planSousRubriques = [
            'PRODUITS D\'INTERÊTS' => [
                [
                    'libelle' => 'Produits d\'intérêts clientèle (+)',
                    'gls' => ['702120000000', '702130000000', '702140000000', '702511000000', '702520000000'],
                ],
                [
                    'libelle' => 'Produits d\'intérêts inter-réseau (+)',
                    'gls' => ['701140000000'],
                ],
                [
                    'libelle' => 'Produits d\'intérêts interbancaires (+)',
                    'gls' => ['701110000000', '701260000000'],
                ],
            ],
            'CHARGES D\'INTERÊTS' => [
                [
                    'libelle' => 'Charges d\'intérêts clientèle (-)',
                    'gls' => ['602520000000', '602530000000'],
                ],
                [
                    'libelle' => 'Charges d\'intérêts inter-réseau (-)',
                    'gls' => ['601780000000'],
                ],
                [
                    'libelle' => 'Charges d\'intérêts interbancaires (-)',
                    'gls' => ['601600000000'],
                ],
                [
                    'libelle' => 'Charges d\'intérêts emprunts (-)',
                    'gls' => ['605320000000'],
                ],
            ],
            'COMMISSIONS NETTES' => [
                [
                    'libelle' => 'Commissions perçues (+)',
                    'gls' => ['702920000000', '702930000000', '707130000000', '707230000000', '707500000000', '707600000000'],
                ],
                [
                    'libelle' => 'Commissions payées (-)',
                    'gls' => ['601400000000', '601930000000'],
                ],
            ],
            'CHARGES D\'EXPLOITATION' => [
                [
                    'libelle' => 'Frais de personnel (-)',
                    'gls' => ['621500000000', '641000000000', '642000000000', '643000000000'],
                ],
                [
                    'libelle' => 'Frais généraux (-)',
                    'gls' => [
                        '601910000000', '604619000000', '611610000000', '611621000000', '611622000000', '611623000000',
                        '612000000000', '621200000000', '621300000000', '621400000000', '621710000000', '621800000000',
                        '622100000000', '622200000000', '622300000000', '622400000000', '622610000000', '622620000000',
                        '622630000000', '622700000000', '623100000000', '623200000000', '623390000000', '630000000000',
                        '631000000000', '632100000000', '632300000000', '632400000000', '632900000000',
                    ],
                ],
                [
                    'libelle' => 'Charges d\'encadrement (-)',
                    'gls' => ['702100000000'],
                ],
                [
                    'libelle' => 'Dotations aux amortissements (-)',
                    'gls' => ['661120000000', '661210000000', '661220000000'],
                ],
            ],
            'PRODUITS D\'EXPLOITATION' => [
                [
                    'libelle' => 'Marge commerciale (+)',
                    'gls' => ['711000000000'],
                ],
                [
                    'libelle' => 'Produits d\'encadrement (+)',
                    'gls' => ['702100000000'],
                ],
                [
                    'libelle' => 'Produits divers d\'exploitation (+)',
                    'gls' => ['725100000000', '728100000000', '728900000000', '729000000000', '740000000000'],
                ],
            ],
            'PROVISIONS POUR RISQUES & CHARGES' => [
                [
                    'libelle' => 'Dotations aux provisions / créances (-)',
                    'gls' => ['664120000000', '664200000000', '664300000000', '666000000000', '669100000000'],
                ],
                [
                    'libelle' => 'Reprises de provisions / créances (+)',
                    'gls' => ['764120000000', '764200000000', '764300000000', '766000000000', '769000000000'],
                ],
            ],
            'RESULTAT EXCEPTIONNEL' => [
                [
                    'libelle' => 'Charges exceptionnelles (-)',
                    'gls' => ['671300000000', '671900000000', '672300000000'],
                ],
            ],
            'Impôt sur le bénéfice (-)' => [
                [
                    'libelle' => 'Impôt sur le bénéfice (-)',
                    'gls' => ['691000000000'],
                ],
            ],
        ];

        foreach ($planSousRubriques as $blocLibelle => $sousRubriques) {
            $bloc = ReferenceCompteBloc::where('libelle', $blocLibelle)->first();
            if (!$bloc) {
                continue;
            }
            foreach ($sousRubriques as $srIndex => $srConfig) {
                $sousRubrique = ReferenceCompteRubrique::firstOrCreate(
                    [
                        'bloc_id' => $bloc->id,
                        'libelle' => $srConfig['libelle'],
                    ],
                    ['sort_order' => $srIndex]
                );
                foreach ($srConfig['gls'] as $glIndex => $glCode) {
                    ReferenceCompteGl::firstOrCreate(
                        [
                            'rubrique_id' => $sousRubrique->id,
                            'numero_gl' => $glCode,
                        ],
                        [
                            'nom_gl' => $srConfig['libelle'],
                            'sort_order' => $glIndex,
                        ]
                    );
                }
            }
        }
    }
}
