from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    path = Path(f"prompts/brains/{name}.md")
    return path.read_text(encoding="utf-8")