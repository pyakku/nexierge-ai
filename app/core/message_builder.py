from app.models.chat_request import ChatRequest
from app.models.openai_message import OpenAIMessage


def build_messages(
    request: ChatRequest,
    system_prompt: str,
    context: str = "",
) -> list[OpenAIMessage]:

    messages = [
        OpenAIMessage(
            role="system",
            content=system_prompt,
        )
    ]

    if context:

        messages.append(
            OpenAIMessage(
                role="system",
                content=f"""
Knowledge Base:

{context}
""".strip(),
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