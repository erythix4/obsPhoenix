#!/bin/bash
MODEL=${OLLAMA_MODEL:-llama3.2}
echo "[ollama] Téléchargement du modèle $MODEL (~2GB, patience)..."
docker compose exec ollama ollama pull $MODEL
echo "[ollama] Modèle $MODEL prêt."
