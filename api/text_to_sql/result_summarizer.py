from __future__ import annotations

import json
import os
from anthropic import Anthropic


def summarize_results(question: str, sql: str, results: list[dict]) -> str:
    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "").startswith("your_"):
        return f"Query returned {len(results)} row(s). Configure ANTHROPIC_API_KEY to generate a Claude summary."
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    compact = json.dumps(results[:50], default=str)[:12000]
    prompt = (
        "Summarize these SQL results in 2-3 plain English sentences for a hospital quality analytics user. "
        f"Question: {question}\nSQL: {sql}\nRows: {compact}"
    )
    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=220, messages=[{"role": "user", "content": prompt}])
    return "".join([block.text for block in resp.content if getattr(block, "type", None) == "text"]).strip()
