import logging
import os

from app.core.context import correlation_id as _cid_var

_SKIP = frozenset({
    "name", "msg", "args", "levelname", "levelno", "pathname",
    "filename", "module", "exc_info", "exc_text", "stack_info",
    "lineno", "funcName", "created", "msecs", "relativeCreated",
    "thread", "threadName", "processName", "process", "taskName",
    "message", "asctime",
})

_W  = "─" * 44
_WW = "═" * 44


def _extra(record: logging.LogRecord) -> dict:
    return {k: v for k, v in record.__dict__.items() if k not in _SKIP and not k.startswith("_")}


class _HumanFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        record.message = record.getMessage()
        msg = record.message
        x = _extra(record)

        if msg == "llm.call":
            tools = x.get("tool_calls") or []
            model = x.get("model", "")
            ms = x.get("latency_ms", "?")
            if tools:
                body = f"  tools : {', '.join(tools)}"
            else:
                body = "  result: direct response"
            return f"\n┌─ LLM  {model}  {ms}ms\n{body}"

        if msg == "tools.round":
            tools = x.get("tools") or []
            r = x.get("round", "?")
            return f"│\n├─ Round {r}  →  {', '.join(tools)}"

        if msg == "tool.executed":
            return f"│  [{x.get('tool', '?')}]  {x.get('latency_ms', '?')}ms"

        if msg == "retriever.complete":
            return (
                f"│    embed {x.get('embedding_ms')}ms  "
                f"pinecone {x.get('pinecone_ms')}ms  "
                f"matches {x.get('matches')}  returned {x.get('returned')}"
            )

        if msg == "knowledge.complete":
            return (
                f"│    xano {x.get('xano_ms')}ms  "
                f"items {x.get('items_returned')}"
            )

        if msg == "media_retriever.complete":
            return (
                f"│    embed {x.get('embedding_ms')}ms  "
                f"pinecone {x.get('pinecone_ms')}ms  "
                f"returned {x.get('returned')}"
            )

        if msg == "media.results":
            items = x.get("items") or []
            lines = [f"│    media found ({len(items)}):"]
            for item in items:
                desc = (item.get("desc") or "")[:80]
                url = (item.get("url") or "").split("/")[-1]
                lines.append(f"│      • {url}  —  {desc}")
            return "\n".join(lines)

        if msg == "tools.executed":
            tools = x.get("tools") or []
            return f"│  done: {', '.join(tools)}  {x.get('latency_ms', '?')}ms total"

        if msg == "workflow.active":
            return f"\n┌─ Workflow  {x.get('workflow')} / {x.get('status')}"

        if msg == "request.complete":
            ms = x.get("latency_ms", "?")
            tools = x.get("tools_called") or []
            tools_str = f"  tools: {', '.join(tools)}" if tools else ""
            return f"└─ done  {ms}ms{tools_str}\n{_W}"

        if record.levelno >= logging.ERROR:
            exc = f"\n{self.formatException(record.exc_info)}" if record.exc_info else ""
            return f"\n{'!'*44}\nERROR  {msg}{exc}\n{'!'*44}"

        if record.levelno >= logging.WARNING:
            return f"[WARN]  {msg}  {x}" if x else f"[WARN]  {msg}"

        return f"[{record.levelname}]  {msg}" + (f"  {x}" if x else "")


class _JsonFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        import json
        record.message = record.getMessage()
        data = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "cid": _cid_var.get(""),
            "logger": record.name,
            "msg": record.message,
        }
        data.update(_extra(record))
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data, default=str)


def setup(level: str = "DEBUG") -> None:
    fmt = os.getenv("LOG_FORMAT", "human")
    handler = logging.StreamHandler()
    handler.setFormatter(_HumanFormatter() if fmt == "human" else _JsonFormatter())

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]

    for noisy in ("httpx", "httpcore", "openai", "pinecone"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
