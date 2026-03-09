"""
dashboard.py -- Rapport de monitoring quotidien RAG
Lancer via : docker compose exec rag-demo python /app/src/dashboard.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import phoenix as px
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console     = Console()
PHOENIX_URL = os.getenv("PHOENIX_BASE_URL", "http://phoenix:6006")


def daily_report(project: str = "rag-security-lab") -> dict:
    client = px.Client(endpoint=PHOENIX_URL)

    try:
        spans = client.get_spans_dataframe(project)
    except Exception as exc:
        console.print(f"[red]Erreur recuperation traces : {exc}[/red]")
        return {}

    if spans.empty:
        console.print("[yellow]Aucune trace trouvee.[/yellow]")
        return {}

    chains = spans[spans["span_kind"] == "CHAIN"]
    llms   = spans[spans["span_kind"] == "LLM"]
    errors = spans[spans["status"] == "ERROR"]

    report = {
        "date":           datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "project":        project,
        "total_traces":   len(chains),
        "total_spans":    len(spans),
        "error_count":    len(errors),
        "error_rate_pct": round(len(errors) / max(len(spans), 1) * 100, 1),
        "avg_latency_ms": round(spans["latency_ms"].mean(), 1),
        "p50_latency_ms": round(spans["latency_ms"].quantile(0.50), 1),
        "p95_latency_ms": round(spans["latency_ms"].quantile(0.95), 1),
    }

    for col, label in [
        ("eval.Hallucination.score", "avg_faithfulness"),
        ("eval.Relevance.score",     "avg_relevance"),
        ("eval.Toxicity.score",      "avg_toxicity"),
    ]:
        if col in spans.columns:
            val = spans[col].dropna()
            report[label] = round(val.mean(), 3) if not val.empty else "N/A"
        else:
            report[label] = "N/A"

    alerts = []
    if report["error_rate_pct"] > 5:
        alerts.append(f"[red]Taux d'erreur {report['error_rate_pct']}% > seuil 5%[/red]")
    if report["p95_latency_ms"] > 3000:
        alerts.append(f"[yellow]P95 {report['p95_latency_ms']}ms > 3s[/yellow]")
    if isinstance(report.get("avg_faithfulness"), float) and report["avg_faithfulness"] < 0.75:
        alerts.append(f"[yellow]Faithfulness {report['avg_faithfulness']:.2f} < 0.75[/yellow]")

    report["alerts"] = alerts
    return report


def print_report(report: dict) -> None:
    if not report:
        return

    console.print(Panel(
        f"[bold]Rapport monitoring RAG[/bold]\n{report['date']} -- {report['project']}",
        style="bold red"
    ))

    t = Table(show_header=True)
    t.add_column("Indicateur")
    t.add_column("Valeur", justify="right")
    for k, v in report.items():
        if k not in ("alerts", "date", "project"):
            t.add_row(k.replace("_", " ").capitalize(), str(v))
    console.print(t)

    if report["alerts"]:
        console.print("\n[bold red]Alertes[/bold red]")
        for a in report["alerts"]:
            console.print(f"  {a}")
    else:
        console.print("\n[green]Aucune alerte -- tout est nominal.[/green]")

    console.print(f"\n[bold]Phoenix UI[/bold] -> {PHOENIX_URL.replace('phoenix','localhost')}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="rag-security-lab")
    args = parser.parse_args()
    r = daily_report(args.project)
    print_report(r)
