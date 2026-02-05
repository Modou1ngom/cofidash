#!/bin/bash

# Script pour redémarrer le service Python Oracle

echo "🔄 Arrêt du service Python Oracle..."

# Trouver et arrêter le processus uvicorn
pkill -f "uvicorn.*main:app" || pkill -f "python3.*main.py" || echo "Aucun processus trouvé"

# Attendre un peu
sleep 2

echo "🚀 Démarrage du service Python Oracle..."

cd "$(dirname "$0")"

# Vérifier si l'environnement virtuel existe
if [ ! -d "venv" ]; then
    echo "❌ L'environnement virtuel n'existe pas."
    echo "Veuillez d'abord exécuter : ./installer.sh"
    exit 1
fi

source venv/bin/activate

# Démarrer en arrière-plan avec uvicorn
nohup uvicorn main:app --host 0.0.0.0 --port 8001 > service.log 2>&1 &

# Attendre que le service démarre (augmenter le délai pour l'initialisation du pool Oracle)
echo "⏳ Attente du démarrage du service..."
sleep 5

# Vérifier que le service est démarré (essayer plusieurs fois)
max_attempts=5
attempt=0
service_ready=false

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8001/ > /dev/null 2>&1; then
        service_ready=true
        break
    fi
    attempt=$((attempt + 1))
    echo "   Tentative $attempt/$max_attempts..."
    sleep 2
done

if [ "$service_ready" = true ]; then
    echo "✅ Service démarré avec succès sur http://localhost:8001"
    echo "📋 Logs disponibles dans: service.log"
    echo "🔍 Test de santé: $(curl -s http://localhost:8001/ | head -c 100)"
else
    echo "❌ Erreur: Le service ne répond pas après $((max_attempts * 2 + 5)) secondes"
    echo "📋 Vérifiez les logs: tail -f service.log"
    echo "📋 Dernières lignes des logs:"
    tail -20 service.log
fi
