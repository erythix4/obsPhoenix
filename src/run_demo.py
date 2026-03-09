"""
run_demo.py -- Serveur FastAPI pour le lab Phoenix RAG
Initialisation lazy : le pipeline RAG se charge au premier appel.
"""
from __future__ import annotations

import logging, os, sys, threading, time, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
logger = logging.getLogger("run_demo")

COLLECTOR = os.getenv("PHOENIX_COLLECTOR_ENDPOINT", "http://localhost:4318")
PROJECT   = os.getenv("PHOENIX_PROJECT_NAME", "rag-security-lab")

DEMO_QUESTIONS = [
    "Qu'est-ce qu'une attaque par prompt injection ?",
    "Comment prevenir le jailbreaking d'un LLM en production ?",
    "Quelles sont les vulnerabilites OWASP Top 10 pour les LLM ?",
    "Qu'est-ce que le RAG poisoning et ses contre-mesures ?",
    "Comment mettre en place des guardrails sur un LLM ?",
    "Qu'est-ce que le model inversion attack ?",
]

_rag       = None
_rag_lock  = threading.Lock()
_rag_ready = False
_rag_error = None


def _init_rag() -> None:
    global _rag, _rag_ready, _rag_error
    with _rag_lock:
        if _rag_ready or _rag_error:
            return
        try:
            logger.info("Chargement du pipeline RAG...")
            from rag_pipeline import build_pipeline
            _rag = build_pipeline(docs_dir="/app/docs")
            _rag_ready = True
            logger.info("Pipeline RAG pret.")
        except Exception as exc:
            _rag_error = str(exc)
            logger.error(f"Erreur init RAG : {exc}", exc_info=True)


def get_rag():
    if _rag_ready:
        return _rag
    if _rag_error:
        raise HTTPException(500, f"Erreur RAG : {_rag_error}")
    threading.Thread(target=_init_rag, daemon=True).start()
    raise HTTPException(503, "RAG en cours de chargement. Reessayez dans 30s.")


app = FastAPI(title="Phoenix Lab RAG API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    logger.info(f"Phoenix projet: {PROJECT}")
    threading.Thread(target=_init_rag, daemon=True).start()
    logger.info("Serveur demarre. RAG en chargement arriere-plan...")


class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    question:   str
    answer:     str
    latency_ms: float


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "rag_ready": _rag_ready, "rag_error": _rag_error}


@app.get("/ready")
async def ready():
    if _rag_ready:
        return {"status": "ready"}
    if _rag_error:
        raise HTTPException(500, f"RAG en erreur : {_rag_error}")
    raise HTTPException(503, "RAG en cours de chargement...")


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    rag = get_rag()
    try:
        t0 = time.time()
        answer = rag.invoke(req.question)
        latency = int((time.time() - t0) * 1000)
        return QueryResponse(question=req.question, answer=answer, latency_ms=latency)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Erreur query: {exc}", exc_info=True)
        raise HTTPException(500, str(exc))


@app.get("/demo")
async def run_demo():
    rag = get_rag()
    results = []
    for q in DEMO_QUESTIONS:
        try:
            t0 = time.time()
            answer = rag.invoke(q)
            latency = int((time.time() - t0) * 1000)
            results.append({"question": q, "answer": answer[:300], "latency_ms": latency})
        except Exception as exc:
            results.append({"question": q, "error": str(exc)})
    return {"project": PROJECT, "results": results, "phoenix_ui": "http://localhost:6006"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["server"], default="server")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    uvicorn.run("run_demo:app", host="0.0.0.0", port=args.port, reload=False)
