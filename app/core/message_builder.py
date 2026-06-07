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
        "Intent Tracking:",
        "Always populate the intent field with a short label for what the guest is asking (e.g. 'greeting', 'breakfast_hours', 'room_service_order', 'handoff_request').",
        "Always populate the intent_reason field with one sentence explaining why you interpreted it that way and what action you took (or will take).",
        "",
        "Language Rule:",
        "Always respond in the same language as the guest's query. This is a hard rule.",
        "",
        "Message History Rule:",
        "Message history is conversational context only. Never use it to determine what the guest is currently asking or what language they are using.",
        "The ONLY source of the guest's current intent and request is the current query. This is a hard rule.",
        "",
        "Links and Media Rule:",
        "Never include any URLs, hyperlinks, markdown links, or image syntax in the response field.",
        "The service_catalog link is delivered via the service_catalog field only — never mention it in response text.",
        "The media array must only contain https image URLs. Never put descriptions or non-URL strings in media.",
        "Never comment on your ability to display, send, share, or provide images. Respond naturally.",
        "If get_media returned no results, say the hotel does not have photos available for that topic.",
        "These are hard rules.",
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
        OpenAIMessage(role="system", content=system_prompt),
        OpenAIMessage(role="system", content=_build_request_settings(request)),
    ]

    if knowledge_context:
        messages.append(OpenAIMessage(
            role="system",
            content=f"Knowledge Base:\n\n{knowledge_context}",
        ))

    if media_context:
        messages.append(OpenAIMessage(
            role="system",
            content=(
                "Media Context:\n\n"
                "This media context is only for selecting or describing images. "
                "Do not include anything from Media Context in data_used.\n\n"
                + media_context
            ),
        ))

    if ordering_context:
        messages.append(OpenAIMessage(
            role="system",
            content=f"Ordering Context:\n\n{ordering_context}",
        ))

    if workflow_context:
        messages.append(OpenAIMessage(role="system", content=workflow_context))

    for message in request.message_history:
        role = "assistant" if message.ai_response else "user"
        messages.append(OpenAIMessage(role=role, content=message.message))

    messages.append(OpenAIMessage(role="user", content=request.query))

    return messages
