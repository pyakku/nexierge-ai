from pathlib import Path


def load_policy(
    name: str,
) -> str:

    path = Path(
        f"prompts/policies/{name}.md"
    )

    return path.read_text(
        encoding="utf-8"
    )