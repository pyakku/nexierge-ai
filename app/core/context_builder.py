def build_context(
    knowledge: list[dict],
) -> str:

    if not knowledge:
        return ""

    return "\n\n".join(
        f"[{item['id']}]\n{item['text']}"
        for item in knowledge
    )