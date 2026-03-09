#!/usr/bin/env python3
import sys, json

try:
    r = json.load(sys.stdin)
except Exception as e:
    print(f"Erreur : {e}")
    sys.exit(1)

if "detail" in r:
    print(f"ERREUR: {r['detail']}")
    sys.exit(1)

print(f"Q : {r['question']}")
print(f"\nR : {r['answer']}")
print(f"\n{r['latency_ms']}ms  |  {r['model']}")
