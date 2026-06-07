import logging
import os
from time import perf_counter

from app.core.openai_client import client
from app.models.router_response import RouterResponse

logger = logging.getLogger(__name__)

_SYSTEM = """You are a hotel AI intent classifier. Classify the guest's message into exactly one category.

SOCIAL — greeting, pleasantry, or small talk with NO hotel question or request:
  "Hi", "Hello", "Good morning", "How are you?", "How are you doing?",
  "How are you doing now?", "Ok", "Okay", "Thanks", "Thank you", "Got it",
  "Great", "Sounds good", "Perfect", "That's nice", "All good?"

HANDOFF — guest explicitly wants to speak to a human, be transferred, or get human support:
  "I want to speak to an agent", "Connect me to reception",
  "I need to talk to someone", "Transfer me to a human"

HOTEL — any question or request about the hotel, even if it starts with a greeting:
  "What time is breakfast?", "Hello, do you have a pool?",
  "Hi, I want to order room service", "Good morning, is the spa open?",
  "Can I see some photos?", "How far is the airport?"

Populate reason with one sentence explaining your classification."""


def route(query: str) -> RouterResponse:
    start = perf_counter()
    try:
        response = client.responses.parse(
            model=os.getenv("ROUTER_MODEL", os.getenv("BRAIN_MODEL", "gpt-4o-mini")),
            input=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": query.strip()},
            ],
            text_format=RouterResponse,
        )
        result = response.output_parsed
        if result is None:
            raise ValueError("Router returned no output")
    except Exception:
        result = RouterResponse(intent="hotel", reason="Router error — defaulting to hotel")

    logger.info(
        "router",
        extra={
            "intent": result.intent,
            "reason": result.reason,
            "latency_ms": int((perf_counter() - start) * 1000),
        },
    )
    return result
