from app.models.chat_request import ChatRequest
from app.models.openai_message import OpenAIMessage


def build_messages(
    request: ChatRequest,
    system_prompt: str,
) -> list[OpenAIMessage]:

    messages = [
        OpenAIMessage(
            role="system",
            content=system_prompt,
        )
    ]

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