# Phoenix Lab — LLM Observability avec Docker

Pipeline RAG sécurité LLM instrumenté avec Arize Phoenix.
Tout tourne localement avec Docker Compose.

## Prérequis

- Docker + Docker Compose v2
- Clé API OpenAI (GPT-4o-mini)
- 4 Go RAM disponibles

## Démarrage en 3 commandes

```bash
# 1. Configurer
make setup
# → Éditer .env et renseigner OPENAI_API_KEY

# 2. Démarrer
make start

# 3. Générer des traces
make demo
```

## URLs

| Service       | URL                         | Description                     |
|---------------|-----------------------------|---------------------------------|
| Lab UI        | http://localhost:3000       | Interface pédagogique HTML      |
| Phoenix UI    | http://localhost:6006       | Traces, évaluations, datasets   |
| RAG API       | http://localhost:8080       | API REST du pipeline RAG        |
| RAG API docs  | http://localhost:8080/docs  | Documentation Swagger           |

## Flux de travail

```
make start          # Démarrer les services
make demo           # Générer des traces (6 questions démo)
                    # → Ouvrir http://localhost:6006 pour voir les traces
make eval           # Lancer les évaluations LLM-as-a-Judge
make dashboard      # Rapport de monitoring
```

## Structure du projet

```
phoenix-lab/
├── docker-compose.yml       # Orchestration des services
├── Dockerfile.rag           # Image de l'app RAG
├── requirements.txt         # Dépendances Python
├── Makefile                 # Commandes lab
├── .env.example             # Template de configuration
│
├── src/
│   ├── rag_pipeline.py      # Pipeline RAG (LangChain + ChromaDB)
│   ├── run_demo.py          # Demo batch + serveur FastAPI
│   ├── evaluate.py          # Évaluations Phoenix
│   └── dashboard.py         # Rapport de monitoring
│
├── docs/                    # Base de connaissances sécurité LLM
│   ├── 01_prompt_injection.txt
│   ├── 02_owasp_llm_top10.txt
│   ├── 03_guardrails.txt
│   └── 04_rag_poisoning_jailbreaking.txt
│
└── nginx/
    ├── lab.html             # Interface pédagogique
    └── nginx.conf           # Proxy vers Phoenix et RAG API
```

## API RAG — Exemples

```bash
# Interroger le RAG
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Qu'\''est-ce que le RAG poisoning ?"}'

# Lancer la démo depuis l'API
curl http://localhost:8080/demo

# Vérifier l'état
curl http://localhost:8080/healthz
```

## Ajouter vos propres documents

Placez des fichiers `.txt` ou `.md` dans le répertoire `docs/`, puis :

```bash
docker compose restart rag-demo
```

## Commandes utiles

```bash
make logs           # Logs en temps réel
make status         # Vérifier l'état de tous les services
make shell-rag      # Shell dans le conteneur RAG
make stop           # Arrêter
make clean          # Supprimer les conteneurs
make reset          # Tout supprimer (données incluses)
```
