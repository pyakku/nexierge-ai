from app.models.chat_request import ChatRequest
from app.models.openai_message import OpenAIMessage


def _build_request_settings(request: ChatRequest) -> str:
    lines = [f"hotel_name={request.hotel_name}"]
    if request.tone:
        lines.append("tone:")
        for key, val in request.tone.items():
            lines.append(f"  {key}={val}")
    lines += [
        "",
        "Greeting Rule:",
        "Only apply this rule when the current query is PURELY a greeting or social pleasantry with NO hotel question whatsoever (e.g. 'hi', 'hello', 'good morning' alone). If the message starts with a greeting AND contains any question or request (e.g. 'Hello, can I see pool pictures?'), it is NOT a pure greeting — treat it as the question it contains and use tools normally.",
        "This is a hard rule — do not override it for any reason. Never upsell anything on pure greetings.",
        "",
        "Intent Tracking:",
        "Always populate the intent field with a short label for what the guest is asking (e.g. 'greeting', 'breakfast_hours', 'room_service_order', 'handoff_request').",
        "Always populate the intent_reason field with one sentence explaining why you interpreted it that way and what action you took (or will take).",
        "",
        "Language Rule:",
        "Always respond in the same language as the guest's query.",
        "This is a hard rule — do not override it for any reason.",
        "",
        "Message History Rule:",
        "Message history is for conversational context only — so the guest does not have to repeat themselves.",
        "Never use message history to determine what the guest is asking, what they want, what language they are using, or what their intent is.",
        "Never treat a past message as the current query.",
        "The ONLY source of the guest's current intent, language, and request is the current query.",
        "If the current query is a greeting or small talk with no question, respond to it as-is — do not infer a request from history.",
        "This is a hard rule — do not override it for any reason.",
        "",
        "Links and Media Rule:",
        "Never include any URLs, hyperlinks, markdown links, or image syntax in the response field — not for images, not for ordering, not for any purpose.",
        "The service_catalog link is delivered separately via the service_catalog field. Never mention or repeat it in the response text.",
        "The media array must only contain image URLs (strings starting with https). Never put descriptions, captions, or any non-URL string into the media array.",
        "Never comment on your ability to display, send, share, or provide images. Respond naturally as if images are visible to the guest.",
        "If the get_media tool returned no results, say the hotel does not currently have photos available for that topic. Never say 'I can't send', 'I can't display', 'I can't share', or 'I can't provide' pictures.",
        "These are hard rules — do not override them for any reason.",
    ]
    return "Request Settings:\n\n" + "\n".join(lines)


def build_messages(
    request: ChatRequest,
    system_prompt: str,
    knowledge_context: str = "",
    media_context: str = "",
    ordering_context: str = "",
    workflow_context: str = "",
) -> list[OpenAIMessage]:

    messages = [
        OpenAIMessage(
            role="system",
            content=system_prompt,
        ),
        OpenAIMessage(
            role="system",
            content=_build_request_settings(request),
        ),
    ]

    if knowledge_context:

        messages.append(
            OpenAIMessage(
                role="system",
                content=f"""
Knowledge Base:

{knowledge_context}
""".strip(),
            )
        )

    if media_context:

        messages.append(
            OpenAIMessage(
                role="system",
                content=f"""
Media Context:

This media context is only for selecting or describing images.
Do not include anything from Media Context in data_used.

{media_context}
""".strip(),
            )
        )

    if ordering_context:

        messages.append(
            OpenAIMessage(
                role="system",
                content=f"""
Ordering Context:

{ordering_context}
""".strip(),
            )
        )

    if workflow_context:

        messages.append(
            OpenAIMessage(
                role="system",
                content=workflow_context,
            )
        )

    for message in request.message_history:

        role = (
            "assistant"
            if message.ai_response
            else "user"
        )

        messages.append(
            OpenAIMessage(
                role=role,
                content=message.message,
            )
        )

    messages.append(
        OpenAIMessage(
            role="system",
            content=(
                "CURRENT QUERY REMINDER — read this before deciding whether to call any tools:\n"
                "The guest's message below is the ONLY input that determines intent, language, and whether to call tools.\n"
                "Message history is context only — never use it to infer what the guest is asking now.\n"
                "If the current message is PURELY a greeting with NO question or request attached "
                "(e.g. 'hi', 'hello', 'مرحبا', 'bonjour', 'hola', 'नमस्ते' — alone with nothing else), "
                "respond with a short friendly greeting only. DO NOT call any tools.\n"
                "If the message starts with a greeting but also contains a question or request, "
                "it is NOT a pure greeting — handle the question normally and use tools as needed."
            ),
        )
    )

    messages.append(
        OpenAIMessage(
            role="user",
            content=request.query,
        )
    )

    return messages
