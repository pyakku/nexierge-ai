from openai import OpenAI

from app.core.openai_client import client


def generate(
    messages: list[dict],
) -> str:

    response = client.responses.create(
        model="gpt-5-mini",
        input=messages,
    )

    return response.output_text