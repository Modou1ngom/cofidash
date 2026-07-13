#!/usr/bin/env bash
# Compile tous les diagrammes PlantUML du chapitre 3.
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

FORMAT="${1:-png}"

compile_jar() {
  local jar="$1"
  java -jar "$jar" -t"$FORMAT" -o "$DIR/out" "$DIR"/*.puml
}

compile_docker() {
  mkdir -p "$DIR/out"
  docker run --rm -v "$DIR:/data" plantuml/plantuml \
    -t"$FORMAT" -o /data/out /data/*.puml
}

mkdir -p "$DIR/out"

if command -v docker &>/dev/null; then
  echo "Compilation via Docker (format: $FORMAT)..."
  compile_docker
elif [[ -f "$DIR/plantuml.jar" ]]; then
  echo "Compilation via plantuml.jar local (format: $FORMAT)..."
  compile_jar "$DIR/plantuml.jar"
elif [[ -f "$HOME/plantuml.jar" ]]; then
  compile_jar "$HOME/plantuml.jar"
else
  echo "Erreur : ni Docker ni plantuml.jar trouvé."
  echo "  Docker : docker pull plantuml/plantuml"
  echo "  JAR    : wget -O $DIR/plantuml.jar https://github.com/plantuml/plantuml/releases/download/v1.2024.8/plantuml-1.2024.8.jar"
  exit 1
fi

echo "Diagrammes générés dans : $DIR/out/"
ls -la "$DIR/out/"
