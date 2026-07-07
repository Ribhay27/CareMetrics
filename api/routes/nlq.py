from __future__ import annotations

import os
import re
from fastapi import APIRouter, HTTPException
from anthropic import Anthropic
from sqlalchemy import text

from api.db import get_engine
from api.models import NLQRequest, NLQResponse
from api.text_to_sql.prompt_builder import build_prompt
from api.text_to_sql.query_validator import validate_query
from api.text_to_sql.result_summarizer import summarize_results

router = APIRouter()


def _strip_sql(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r"^```sql\s*", "", raw, flags=re.I)
    raw = re.sub(r"^```\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return raw.strip()


def _claude_sql(question: str, extra_error: str | None = None) -> str:
    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "").startswith("your_"):
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY is not configured")
    messages = build_prompt(question)
    if extra_error:
        messages[-1]["content"] += f"\n\nPrevious SQL failed validation: {extra_error}\nReturn corrected SQL only."
    system = messages[0]["content"]
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    resp = client.messages.create(model="claude-sonnet-4-6", max_tokens=700, system=system, messages=[messages[1]])
    return _strip_sql("".join([block.text for block in resp.content if getattr(block, "type", None) == "text"]))


@router.post("/query", response_model=NLQResponse)
def query(req: NLQRequest):
    error = None
    sql = ""
    for _ in range(3):
        sql = _claude_sql(req.question, error)
        ok, error = validate_query(sql)
        if ok:
            break
    else:
        raise HTTPException(status_code=400, detail={"error": "Could not generate valid SQL", "last_sql": sql, "validation_error": error})
    with get_engine().connect() as conn:
        rows = [dict(r) for r in conn.execute(text(sql)).mappings().fetchmany(50)]
    summary = summarize_results(req.question, sql, rows)
    return NLQResponse(question=req.question, generated_sql=sql, results=rows, plain_english_summary=summary)
