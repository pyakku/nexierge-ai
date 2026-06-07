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
        "Language Rule:",
        "Always respond in the same language as the guest's query.",
        "This is a hard rule — do not override it for any reason.",
        "",
        "Message History Rule:",
        "Message history is provided for conversational context only.",
        "Never extract facts, information, language, or intent from message history.",
        "Always determine language and intent from the current query only.",
        "This is a hard rule — do not override it for any reason.",
        "",
        "Links and Media Rule:",
        "Never include any URLs, hyperlinks, markdown links, or image syntax in the response field — not for images, not for ordering, not for any purpose.",
        "The service_catalog link is delivered separately via the service_catalog field. Never mention or repeat it in the response text.",
        "The media array must only contain image URLs (strings starting with https). Never put descriptions, captions, or any non-URL string into the media array.",
        "Never comment on your ability to display images. Respond naturally as if images are visible to the guest.",
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
            role="user",
            content=request.query,
        )
    )

    return messages
