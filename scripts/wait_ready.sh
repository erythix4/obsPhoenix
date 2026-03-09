#!/bin/bash
# Attend que /ready retourne 200 (RAG charge et pret)
MAX=90   # secondes max
STEP=5

echo "[wait] RAG en cours de chargement..."

for i in $(seq 1 $((MAX/STEP))); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ready 2>/dev/null)
    if [ "$STATUS" = "200" ]; then
        echo "[wait] RAG pret."
        exit 0
    fi

    # Verifier si erreur fatale
    ERROR=$(curl -s http://localhost:8080/healthz 2>/dev/null | python3 -c \
        "import sys,json; d=json.load(sys.stdin); print(d.get('rag_error') or '')" 2>/dev/null)
    if [ -n "$ERROR" ]; then
        echo ""
        echo "ERREUR fatale du pipeline RAG :"
        echo "  $ERROR"
        echo ""
        echo "Verifiez : make logs-rag"
        exit 1
    fi

    echo "  ...attente ($((i*STEP))s / ${MAX}s) statut HTTP: $STATUS"
    sleep $STEP
done

echo ""
echo "TIMEOUT: le RAG n'a pas demarre en ${MAX}s."
echo "Verifiez : make logs-rag"
exit 1
