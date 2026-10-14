"""
Check the assistant against tests/eval_set.json WITHOUT calling an LLM.
  - in-scope questions: is an acceptable source file in the top-3 retrieved passages?
  - out-of-scope questions: does the assistant refuse (no answer from documents)?
Run:  python eval_rag.py          (add --verbose to see scores)
"""
import json
import sys
from pathlib import Path

from rag_chat.service import RagService

verbose = "--verbose" in sys.argv
data = json.loads((Path(__file__).parent / "tests" / "eval_set.json").read_text(encoding="utf-8"))
svc = RagService()
print(f"retriever={svc.retriever.name}  passages={len(svc.chunks)}  min_score={svc.min_score}  min_coverage={svc.min_coverage}\n")

hits = 0
for item in data["in_scope"]:
    found = svc.retriever.search(item["q"], 3)
    ok = bool(found) and any(any(tag in c.source for tag in item["sources"]) for c, _ in found) \
        and not svc.ask(item["q"], use_llm=False)["mode"] == "refused"
    hits += ok
    top = f"{found[0][0].source} ({found[0][1]:.2f})" if found else "nothing"
    if verbose or not ok:
        print(("PASS " if ok else "FAIL ") + item["q"] + "\n       top: " + top)
print(f"\nIn-scope retrieval: {hits}/{len(data['in_scope'])}")

refused = 0
for q in data["out_of_scope"]:
    r = svc.ask(q, use_llm=False)
    ok = not r["grounded"]
    refused += ok
    if verbose or not ok:
        top = svc.retriever.search(q, 1)
        print(("PASS " if ok else "FAIL ") + q + (f"\n       top score {top[0][1]:.2f}" if top else "\n       no overlap"))
print(f"Out-of-scope refused: {refused}/{len(data['out_of_scope'])}")

sys.exit(0 if hits >= 0.9 * len(data["in_scope"]) and refused == len(data["out_of_scope"]) else 1)
