# Diagrammes PlantUML — Chapitre 3 COFIdash

## Fichiers disponibles

| Fichier | Diagramme | Figure |
|---------|-----------|--------|
| `01_architecture_generale.puml` | Architecture en couches | Figure 3.1 |
| `02_cas_utilisation.puml` | Cas d'utilisation | Figure 3.2 |
| `03_classes_applicatives.puml` | Classes applicatives Laravel | Figure 3.3 |
| `04_sequence_kpi_dashboard.puml` | Séquence consultation KPI | Figure 3.4 |
| `05_sequence_sync_c360.puml` | Séquence synchronisation C360 | Figure 3.5 |
| `06_activite_objectifs.puml` | Activité validation objectifs | Figure 3.6 |
| `07_dimensions_faits.puml` | Dimensions et faits | Figure 3.7 |
| `08_etoile_production_credit.puml` | Schéma en étoile production | Figure 3.8 |
| `09_deploiement.puml` | Déploiement | Figure 3.9 |
| `10_sequence_vue360_clients.puml` | Séquence Vue 360 clients | Figure 3.10 |

## Compilation

### Option 1 — JAR PlantUML (local)

```bash
# Prérequis : Java + plantuml.jar
# Téléchargement : https://plantuml.com/download

cd docs/plantuml
java -jar plantuml.jar -tpng *.puml
java -jar plantuml.jar -tsvg *.puml
```

Les images sont générées dans le même dossier (`*.png` ou `*.svg`).

### Option 2 — Docker

```bash
cd docs/plantuml
docker run --rm -v "$(pwd):/data" plantuml/plantuml -tpng /data/*.puml
docker run --rm -v "$(pwd):/data" plantuml/plantuml -tsvg /data/*.puml
```

### Option 3 — Extension VS Code / Cursor

Installer l'extension **PlantUML** (jebbs.plantuml), puis :
- `Alt+D` pour prévisualiser
- Export PNG/SVG via la palette de commandes

### Option 4 — Serveur en ligne

Copier le contenu d'un fichier `.puml` sur [https://www.plantuml.com/plantuml](https://www.plantuml.com/plantuml).

## Script de compilation rapide

```bash
./docs/plantuml/compile.sh
```

## Insertion dans Word

1. Compiler en PNG (300 dpi recommandé pour impression) :
   ```bash
   java -jar plantuml.jar -tpng -Sdpi=300 docs/plantuml/*.puml
   ```
2. Insérer les images dans `docs/Chapitre3_COFIdash.docx` (Insertion → Image).

## Dépendances graphiques (optionnel)

Pour les diagrammes de déploiement et certains composants, Graphviz améliore le rendu :

```bash
sudo apt install graphviz   # Debian/Ubuntu
```
