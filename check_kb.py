from app.kb_service import search_knowledge_base

queries = [
    "How much is the table zit and when do I need to pay the rest?",
    "What happens if the weather is bad for your event."
]

with open('kb_results.txt', 'w', encoding='utf-8') as f:
    for q in queries:
        f.write(f"=== QUERY: {q} ===\n")
        res = search_knowledge_base(q, top_k=10)
        for r in res:
            f.write(f"Score: {r['score']}\nText: {r['text']}\n---\n")


with open('kb_results.txt', 'w', encoding='utf-8') as f:
    for q in queries:
        f.write(f"=== QUERY: {q} ===\n")
        res = search_knowledge_base(q, top_k=10)
        for r in res:
            f.write(f"Score: {r['score']}\nText: {r['text']}\n---\n")

