from app.models.chat_request import ChatRequest
from app.models.openai_message import OpenAIMessage


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
            content=f"""
Request Settings:

hotel_name={request.hotel_name}
tone={request.tone}

Language Rule:
Always respond in the same language as the guest's query.
This is a hard rule — do not override it for any reason.
""".strip(),
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
