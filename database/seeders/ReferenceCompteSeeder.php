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

        // Sous-rubrique "Charges d'encadrement (-)" sous PRODUITS D'INTÉRÊTS
        $blocProduitsInterets = ReferenceCompteBloc::where('libelle', 'PRODUITS D\'INTERÊTS')
            ->orWhere('libelle', 'PRODUITS D\'INTÉRÊTS')
            ->first();
        if ($blocProduitsInterets) {
            $sousRubrique = ReferenceCompteRubrique::firstOrCreate(
                [
                    'bloc_id' => $blocProduitsInterets->id,
                    'libelle' => 'Charges d\'encadrement (-)',
                ],
                ['sort_order' => 0]
            );
            if ($sousRubrique->gls()->count() === 0) {
                ReferenceCompteGl::create([
                    'rubrique_id' => $sousRubrique->id,
                    'numero_gl' => '702100000000',
                    'nom_gl' => 'Charges d\'encadrement (à configurer)',
                    'sort_order' => 0,
                ]);
            }
        }
    }
}
