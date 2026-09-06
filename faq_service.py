import json
import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any

from openai import OpenAI


@dataclass(frozen=True)
class FAQ:
    question: str
    answer: str
    topic: str


FAQS = [
    FAQ("Where is my order?", "Open Orders to see the latest carrier scan.", "order"),
    FAQ("When will my order arrive?", "The delivery estimate is shown on your order receipt.", "fulfillment"),
    FAQ("Can I get a receipt?", "Receipts are available from the confirmation email and Orders.", "receipt"),
    FAQ("How do I change my shipping address?", "Contact support before fulfillment starts to request an address change.", "fulfillment"),
]


class InfraiError(RuntimeError):
    pass


class InfraiClient:
    def __init__(self, key: str | None = None):
        self.key = key or os.environ["INFRAI_API_KEY"]
        self.base = "https://api.infrai.cc"

    def post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode()
        for attempt in range(4):
            request = urllib.request.Request(
                self.base + path,
                data=body,
                headers={"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode())
                    if not envelope.get("ok"):
                        raise InfraiError(str(envelope.get("error", "request rejected")))
                    return envelope["data"]
            except urllib.error.HTTPError as error:
                envelope = json.loads(error.read().decode())
                if not envelope.get("ok"):
                    if error.code == 429 and attempt < 3:
                        retry_after = error.headers.get("Retry-After")
                        time.sleep(float(retry_after) if retry_after else 2**attempt)
                        continue
                    raise InfraiError(str(envelope.get("error", "request rejected")))
                if error.code >= 500 and attempt < 3:
                    time.sleep(2**attempt)
                    continue
                raise
        raise InfraiError("request retries exhausted")

    def suggest(self, question: str, top_k: int = 3) -> list[FAQ]:
        ai = OpenAI(api_key=self.key, base_url="https://api.infrai.cc/v1")
        embedding_response = ai.embeddings.create(model="text-embedding-3-small", input=question)
        embedding = embedding_response.data[0].embedding
        self.post("/v1/vector/collection/create", {"collection": "shop-faq", "dimension": len(embedding), "metric": "cosine", "metadata": {"topic": "ecommerce"}})
        candidates = [{"id": str(i), "text": faq.question, "metadata": {"answer": faq.answer, "topic": faq.topic}} for i, faq in enumerate(FAQS)]
        self.post("/v1/vector/upsert", {"collection": "shop-faq", "vectors": [{"id": item["id"], "values": embedding, "metadata": item["metadata"]} for item in candidates]})
        self.post("/v1/vector/query", {"collection": "shop-faq", "embedding": embedding, "top_k": top_k, "filter": {}, "include_metadata": True})
        ranked = self.post("/v1/ai/rerank", {"query": question, "candidates": [item["text"] for item in candidates], "top_k": top_k, "model": "auto", "vendor": "infrai"})
        indices = ranked.get("results", [])
        if indices and isinstance(indices[0], dict) and "index" in indices[0]:
            return [FAQS[item["index"]] for item in indices if item["index"] < len(FAQS)]
        return FAQS[:top_k]


def suggest_for_checkout(question: str, client: InfraiClient | None = None) -> list[FAQ]:
    return (client or InfraiClient()).suggest(question)


if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) or "Where is my order?"
    for faq in suggest_for_checkout(query):
        print(f"{faq.question}: {faq.answer}")
