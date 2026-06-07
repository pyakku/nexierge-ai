from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=None)
def load_policy(
    name: str,
) -> str:

    path = Path(
        f"prompts/policies/{name}.md"
    )

    return path.read_text(
        encoding="utf-8"
    )