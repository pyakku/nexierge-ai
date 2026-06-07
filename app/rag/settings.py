import os

TOP_K = 10

MAX_CONTEXT_ITEMS = 3

SCORE_RATIO = 0.7

# Absolute minimum cosine similarity for media results.
# Items below this score are dropped even if they top the relative ranking.
# Tune via MEDIA_MIN_SCORE env var after reviewing logged scores.
MEDIA_MIN_SCORE = float(os.getenv("MEDIA_MIN_SCORE", "0.45"))