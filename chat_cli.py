"""Terminal chat:  python chat_cli.py   (type 'quit' to exit)"""
from rag_chat import llm
from rag_chat.service import RagService

svc = RagService()
print(f"Sentry QC assistant | {len(svc.chunks)} passages | retriever={svc.retriever.name} | LLM={llm.provider()}")
print("Ask a question (or 'quit').\n")
history = []
while True:
    try:
        q = input("you> ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if q.lower() in {"quit", "exit", "q"}:
        break
    if not q:
        continue
    r = svc.ask(q, history)
    print("\n" + r["answer"])
    for s in r["sources"]:
        print(f"   [{s['n']}] {s['source']} > {s['heading']}  (score {s['score']})")
    print()
    history += [{"role": "user", "content": q}, {"role": "assistant", "content": r["answer"]}]
