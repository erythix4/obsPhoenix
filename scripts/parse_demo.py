#!/usr/bin/env python3
import sys, json

try:
    data = json.load(sys.stdin)
except Exception as e:
    print(f"Erreur lecture JSON : {e}")
    sys.exit(1)

results = data.get("results", [])
print(f"  Projet  : {data.get('project', '?')}")
print(f"  Requetes: {len(results)}\n")

for r in results:
    q = r["question"][:65]
    if "answer" in r:
        a = r["answer"][:100].replace("\n", " ")
        ms = r.get("latency_ms", "?")
        print(f"  OK  {q}")
        print(f"      {a}...")
        print(f"      {ms}ms\n")
    else:
        print(f"  ERR {q}")
        print(f"      {r.get('error', '?')}\n")

print("  Traces -> http://localhost:6006")
