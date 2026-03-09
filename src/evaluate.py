"""
evaluate.py -- Evaluations LLM-as-a-Judge avec Phoenix
Lancer via : docker compose exec rag-demo python /app/src/evaluate.py
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import phoenix as px
from phoenix.evals import (
    HallucinationEvaluator,
    RelevanceEvaluator,
    ToxicityEvaluator,
    run_evals,
    OpenAIModel,
)
from rich.console import Console
from rich.table import Table

logger  = logging.getLogger(__name__)
console = Console()

PHOENIX_URL = os.getenv("PHOENIX_BASE_URL", "http://phoenix:6006")


def run_evaluations(project: str = "rag-security-lab") -> None:
    console.print(f"\n[bold]Evaluations Phoenix[/bold] -- projet : {project}")

    try:
        client = px.Client(endpoint=PHOENIX_URL)
    except Exception as exc:
        console.print(f"[red]Connexion Phoenix impossible : {exc}[/red]")
        sys.exit(1)

    try:
        spans_df = client.get_spans_dataframe(project)
    except Exception as exc:
        console.print(f"[red]Impossible de recuperer les traces : {exc}[/red]")
        console.print("[yellow]Lancez d'abord : make demo[/yellow]")
        sys.exit(1)

    llm_spans = spans_df[
        (spans_df["span_kind"] == "LLM") &
        (spans_df["input.value"].notna()) &
        (spans_df["output.value"].notna())
    ].copy()

    if llm_spans.empty:
        console.print("[yellow]Aucun span LLM trouve. Lancez d'abord : make demo[/yellow]")
        sys.exit(0)

    console.print(f"  {len(llm_spans)} spans LLM recuperes")

    eval_model = OpenAIModel(model="gpt-4o-mini", temperature=0)

    results = run_evals(
        dataframe=llm_spans,
        evaluators=[
            HallucinationEvaluator(eval_model),
            RelevanceEvaluator(eval_model),
            ToxicityEvaluator(eval_model),
        ],
        provide_explanation=True,
        concurrency=4,
    )

    px.log_evaluations(*results, project_name=project)
    console.print("[green]Evaluations loguees dans Phoenix.[/green]")

    table = Table(title="Resume des evaluations")
    table.add_column("Metrique")
    table.add_column("Moyenne", justify="right")
    table.add_column("Min",     justify="right")
    table.add_column("Max",     justify="right")

    for df, name in zip(results, ["Hallucination", "Relevance", "Toxicity"]):
        scores = df["score"].dropna()
        if not scores.empty:
            table.add_row(name,
                f"{scores.mean():.3f}", f"{scores.min():.3f}", f"{scores.max():.3f}")

    console.print(table)
    console.print(f"\n[bold]Resultats[/bold] -> {PHOENIX_URL.replace('phoenix','localhost')}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="rag-security-lab")
    args = parser.parse_args()
    run_evaluations(args.project)
