"""AI-assisted support-ticket triage automation.

The project runs in a free deterministic demo mode by default. When an
OPENAI_API_KEY is available, pass --use-ai to classify tickets with an LLM.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE_DIR / "data" / "sample_tickets.csv"
DEFAULT_KNOWLEDGE_BASE = BASE_DIR / "data" / "knowledge_base.json"
DEFAULT_OUTPUT = BASE_DIR / "output" / "triaged_tickets.csv"

CATEGORIES = ("account_access", "billing", "technical", "general")
PRIORITIES = ("low", "medium", "high", "urgent")


def load_knowledge_base(path: Path) -> list[dict[str, Any]]:
    """Load reusable support guidance from a JSON knowledge base."""
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("Knowledge base must be a JSON list.")
    return data


def retrieve_context(message: str, articles: list[dict[str, Any]]) -> dict[str, Any]:
    """Return the most relevant article using transparent keyword scoring."""
    message_words = set(re.findall(r"[a-z0-9]+", message.lower()))
    best_article: dict[str, Any] | None = None
    best_score = 0

    for article in articles:
        keywords = {word.lower() for word in article.get("keywords", [])}
        score = len(message_words & keywords)
        if score > best_score:
            best_score = score
            best_article = article

    return best_article or {
        "id": "KB-000",
        "title": "General support routing",
        "guidance": "Acknowledge the customer, summarize the issue, and route it for review.",
    }


def demo_analyze(ticket: dict[str, str], article: dict[str, Any]) -> dict[str, str]:
    """Classify a ticket locally so the project can be tested without API costs."""
    message = ticket["message"].lower()

    if any(word in message for word in ("password", "login", "locked", "sign in")):
        category = "account_access"
    elif any(word in message for word in ("charged", "charge", "invoice", "refund", "billing")):
        category = "billing"
    elif any(word in message for word in ("error", "crash", "broken", "failed", "not working")):
        category = "technical"
    else:
        category = "general"

    if any(word in message for word in ("security", "fraud", "emergency", "outage")):
        priority = "urgent"
    elif any(word in message for word in ("cannot", "can't", "locked", "charged twice", "crash")):
        priority = "high"
    elif any(word in message for word in ("help", "problem", "issue", "refund")):
        priority = "medium"
    else:
        priority = "low"

    negative_words = ("angry", "frustrated", "terrible", "cannot", "can't", "wrong")
    sentiment = "negative" if any(word in message for word in negative_words) else "neutral"

    summary = ticket["message"].strip()
    if len(summary) > 100:
        summary = summary[:97].rstrip() + "..."

    return {
        "category": category,
        "priority": priority,
        "sentiment": sentiment,
        "summary": summary,
        "knowledge_article": article["id"],
        "draft_response": (
            f"Hello {ticket['customer_name']}, thank you for contacting support. "
            f"I understand your concern. Based on {article['id']}, {article['guidance']} "
            "A support specialist will review the details before this response is sent."
        ),
    }


def ai_analyze(ticket: dict[str, str], article: dict[str, Any], model: str) -> dict[str, str]:
    """Use the OpenAI Responses API and validate the returned JSON."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install dependencies with: pip install -r requirements.txt") from exc

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing. Use demo mode or configure the key.")

    client = OpenAI()
    prompt = f"""
You triage customer-support tickets. Return only valid JSON with these keys:
category, priority, sentiment, summary, knowledge_article, draft_response.

Allowed category values: {', '.join(CATEGORIES)}
Allowed priority values: {', '.join(PRIORITIES)}
Sentiment must be positive, neutral, or negative.
Keep the summary under 25 words. The draft response must be professional,
must not promise a refund or resolution, and must say a human will review it.

Customer: {ticket['customer_name']}
Subject: {ticket['subject']}
Message: {ticket['message']}

Retrieved knowledge article:
ID: {article['id']}
Title: {article['title']}
Guidance: {article['guidance']}
""".strip()

    response = client.responses.create(model=model, input=prompt)
    raw_text = response.output_text.strip()
    raw_text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.IGNORECASE)
    result = json.loads(raw_text)
    validate_result(result)
    return {key: str(value) for key, value in result.items()}


def validate_result(result: dict[str, Any]) -> None:
    required = {
        "category",
        "priority",
        "sentiment",
        "summary",
        "knowledge_article",
        "draft_response",
    }
    missing = required - result.keys()
    if missing:
        raise ValueError(f"Model response is missing: {', '.join(sorted(missing))}")
    if result["category"] not in CATEGORIES:
        raise ValueError(f"Unexpected category: {result['category']}")
    if result["priority"] not in PRIORITIES:
        raise ValueError(f"Unexpected priority: {result['priority']}")


def process_tickets(
    input_path: Path,
    output_path: Path,
    knowledge_base_path: Path,
    use_ai: bool = False,
    model: str = "gpt-5.6-luna",
) -> int:
    """Read tickets, enrich them, and write a CSV data-pipeline output."""
    articles = load_knowledge_base(knowledge_base_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open(newline="", encoding="utf-8") as source:
        tickets = list(csv.DictReader(source))

    required_columns = {"ticket_id", "customer_name", "subject", "message"}
    if not tickets:
        raise ValueError("Input CSV contains no tickets.")
    missing_columns = required_columns - tickets[0].keys()
    if missing_columns:
        raise ValueError(f"Input CSV is missing: {', '.join(sorted(missing_columns))}")

    fieldnames = list(tickets[0].keys()) + [
        "category",
        "priority",
        "sentiment",
        "summary",
        "knowledge_article",
        "draft_response",
        "processing_mode",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames)
        writer.writeheader()
        for ticket in tickets:
            article = retrieve_context(ticket["subject"] + " " + ticket["message"], articles)
            analysis = ai_analyze(ticket, article, model) if use_ai else demo_analyze(ticket, article)
            writer.writerow({**ticket, **analysis, "processing_mode": "ai" if use_ai else "demo"})

    return len(tickets)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Triage support tickets into an enriched CSV.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--knowledge-base", type=Path, default=DEFAULT_KNOWLEDGE_BASE)
    parser.add_argument("--use-ai", action="store_true", help="Call the OpenAI API instead of demo mode.")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = process_tickets(
        input_path=args.input,
        output_path=args.output,
        knowledge_base_path=args.knowledge_base,
        use_ai=args.use_ai,
        model=args.model,
    )
    mode = "AI" if args.use_ai else "demo"
    print(f"Processed {count} tickets in {mode} mode.")
    print(f"Output saved to: {args.output}")


if __name__ == "__main__":
    main()
