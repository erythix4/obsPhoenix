SHELL := /bin/bash
.PHONY: build up down demo query pull-model logs status clean

build:
	docker compose build

pull-model:
	@bash scripts/pull_model.sh

up:
	docker compose up -d
	@echo '[info] Phoenix  : http://localhost:6006'
	@echo '[info] Lab UI   : http://localhost:3000'
	@echo '[info] RAG API  : http://localhost:8080'
	@echo '[info] 1ere fois : make pull-model  (~2GB)'

demo:
	@echo '[demo] Attente que le RAG soit disponible...'
	@bash scripts/wait_ready.sh
	@curl -sf http://localhost:8080/demo | python3 scripts/parse_demo.py

query:
	@test -n '$(Q)' || (echo 'Usage: make query Q="votre question"' && exit 1)
	@curl -sf -G http://localhost:8080/query --data-urlencode 'q=$(Q)' | python3 scripts/parse_query.py

logs:
	docker compose logs -f rag-demo

status:
	docker compose ps

down:
	docker compose down

clean:
	docker compose down -v
