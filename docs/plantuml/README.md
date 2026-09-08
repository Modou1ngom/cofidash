# Diagrammes PlantUML — Chapitre 3 COFIdash

Les cas d’utilisation, séquences et activités sont **un diagramme par profil utilisateur**.

Profils du code (`ProfileSeeder` / `profiles.js`) : **MD**, **DGA**, **RESPONSABLE_ZONE**, **CHEF_AGENCE**, **CAF**, **CC**, **FINANCES**, **EXPLOITATIONS**, **ADMIN**.

## Fichiers

### Synthèse (pas propres à un profil)

| Fichier | Diagramme | Figure |
|---------|-----------|--------|
| `01_architecture_generale.puml` | Architecture en couches | 3.1 |
| `02_cas_utilisation.puml` | Carte des acteurs | 3.2 |
| `03_classes_applicatives.puml` | Classes applicatives Laravel | 3.3 |
| `05_sequence_sync_c360.puml` | Séquence C360 (acteur : CAF mobile) | 3.5 |
| `06_activite_objectifs.puml` | Activité chaînée (couloirs par user) | 3.6 |
| `07_dimensions_faits.puml` | Dimensions et faits | 3.7 |
| `08_etoile_production_credit.puml` | Schéma en étoile production | 3.8 |
| `09_deploiement.puml` | Déploiement | 3.9 |
| `10_sequence_vue360_clients.puml` | Séquence liste clients (acteur : CAF) | 3.10 |

### Cas d’utilisation par utilisateur

| Fichier | Acteur | Figure |
|---------|--------|--------|
| `02a_uc_md.puml` | Directeur Général (MD) | 3.2a |
| `02b_uc_dga.puml` | DGA | 3.2b |
| `02c_uc_responsable_zone.puml` | Responsable Zone | 3.2c |
| `02d_uc_chef_agence.puml` | Chef d’Agence | 3.2d |
| `02e_uc_caf.puml` | CAF | 3.2e |
| `02f_uc_cc.puml` | Conseiller Client | 3.2f |
| `02g_uc_finances.puml` | Finances | 3.2g |
| `02h_uc_exploitations.puml` | Exploitations | 3.2h |
| `02i_uc_admin.puml` | Administrateur | 3.2i |

### Séquences par utilisateur

| Fichier | Acteur / flux | Figure |
|---------|---------------|--------|
| `04_sequence_kpi_dashboard.puml` | MD — consultation KPI | 3.4a |
| `04b_sequence_dga_objectif.puml` | DGA — création objectif territoire | 3.4b |
| `04c_sequence_md_validation.puml` | MD — validation objectif DGA | 3.4c |
| `04d_sequence_responsable_zone.puml` | Responsable Zone + DGA | 3.4d |
| `04e_sequence_chef_agence.puml` | Chef d’agence + Resp. Zone | 3.4e |
| `04f_sequence_caf.puml` | CAF — objectifs et KPI | 3.4f |
| `04g_sequence_cc.puml` | CC — Vue 360 | 3.4g |
| `04h_sequence_finances.puml` | Finances — CR par agence | 3.4h |
| `04i_sequence_admin.puml` | Admin — création utilisateur | 3.4i |
| `04j_sequence_exploitations.puml` | Exploitations — lecture KPI | 3.4j |

### Activités par utilisateur

| Fichier | Acteur | Figure |
|---------|--------|--------|
| `06a_activite_md.puml` | MD | 3.6a |
| `06b_activite_dga.puml` | DGA | 3.6b |
| `06c_activite_responsable_zone.puml` | Responsable Zone | 3.6c |
| `06d_activite_chef_agence.puml` | Chef d’Agence | 3.6d |
| `06e_activite_caf.puml` | CAF | 3.6e |
| `06f_activite_cc.puml` | CC | 3.6f |
| `06g_activite_finances.puml` | Finances | 3.6g |
| `06h_activite_exploitations.puml` | Exploitations | 3.6h |
| `06i_activite_admin.puml` | Admin | 3.6i |

Le style est **intégré dans chaque `.puml`** : vous pouvez coller un fichier tel quel sur https://www.plantuml.com/plantuml/uml/ (plus de `!include`).

## Compilation

```bash
./docs/plantuml/compile.sh
```

Ou :

```bash
cd docs/plantuml
java -jar plantuml.jar -tpng -o out *.puml
```

Les PNG sont écrits dans `docs/plantuml/out/`.

## Insertion dans Word

1. Compiler en PNG (300 dpi pour impression) :
   ```bash
   java -jar docs/plantuml/plantuml.jar -tpng -Sdpi=300 -o out docs/plantuml/*.puml
   ```
2. Insérer les images dans le chapitre 3 (Insertion → Image).
3. Légende type : *Figure 3.2a — Cas d’utilisation du Directeur Général (MD)*.
