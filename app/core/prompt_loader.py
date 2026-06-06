from pathlib import Path


def load_prompt(name: str) -> str:
    path = Path(f"prompts/brains/{name}.md")
    return path.read_text(encoding="utf-8")