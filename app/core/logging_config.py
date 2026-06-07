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


def _extra(record: logging.LogRecord) -> dict:
    return {k: v for k, v in record.__dict__.items() if k not in _SKIP and not k.startswith("_")}


class _HumanFormatter(logging.Formatter):

    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()
        msg = record.message
        x = _extra(record)

        if msg == "llm.call":
            tools = x.get("tool_calls") or []
            lines = ["\n----LLM----"]
            lines.append(f"tools: {', '.join(tools)}" if tools else "direct response")
            lines.append(f"{x.get('latency_ms', '?')}ms")
            return "\n".join(lines)

        if msg == "tools.round":
            tools = x.get("tools") or []
            return f"\n----Tools (round {x.get('round', '?')})----\ncalling: {', '.join(tools)}"

        if msg == "tool.executed":
            return f"  {x.get('tool', '?')}  {x.get('latency_ms', '?')}ms"

        if msg == "request.complete":
            return f"\nTotal: {x.get('latency_ms', '?')}ms\n{'─' * 40}"

        if msg == "retriever.complete":
            return (
                f"  retriever  embed={x.get('embedding_ms')}ms  "
                f"pinecone={x.get('pinecone_ms')}ms  "
                f"matches={x.get('matches')}  returned={x.get('returned')}"
            )

        if msg == "knowledge.complete":
            return (
                f"  knowledge  retrieval={x.get('retrieval_ms')}ms  "
                f"xano={x.get('xano_ms')}ms  "
                f"items={x.get('items_returned')}"
            )

        if msg == "media_retriever.complete":
            return (
                f"  media  embed={x.get('embedding_ms')}ms  "
                f"pinecone={x.get('pinecone_ms')}ms  "
                f"returned={x.get('returned')}"
            )

        if msg == "workflow.active":
            return f"\n----Workflow----\n{x.get('workflow')} / {x.get('status')}"

        if msg == "tools.executed":
            tools = x.get("tools") or []
            return f"  done: {', '.join(tools)}  {x.get('latency_ms', '?')}ms"

        if record.exc_info:
            return f"[ERROR] {msg}\n{self.formatException(record.exc_info)}"

        if x:
            return f"[{record.levelname}] {msg}  {x}"
        return f"[{record.levelname}] {msg}"


class _JsonFormatter(logging.Formatter):
    import json as _json

    def format(self, record: logging.LogRecord) -> str:
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

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("pinecone").setLevel(logging.WARNING)
