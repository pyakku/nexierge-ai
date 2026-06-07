import logging
import re
from time import perf_counter

from app.brains.router import get_brain_name
from app.core.intent_router import route
from app.core.llm import generate, generate_with_tools
from app.core.message_builder import build_messages
from app.core.policy_loader import load_policy
from app.core.prompt_loader import load_prompt
from app.core.workflow_finder import get_active_workflow
from app.models.agent_response import AgentResponse, ServiceCatalog
from app.models.chat_request import ChatRequest
from app.tools.executor import ToolExecutor
from app.tools.registry import get_tool_definitions

logger = logging.getLogger(__name__)

_MAX_TOOL_ROUNDS = 3
_ONE_SHOT_TOOLS = frozenset({"get_answers", "get_media", "get_service_catalogs", "room_details"})


class Agent:

    HANDOFF_WORKFLOW = "handoff"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    HANDOFF_SUCCESS = "handoff_success"
    HANDOFF_CANCELLED = "handoff_cancelled"

    def __init__(self):
        self.tool_executor = ToolExecutor()

    def respond(self, request: ChatRequest) -> AgentResponse:
        start = perf_counter()
        brain = get_brain_name(request.brain_id)

        #
        # ACTIVE WORKFLOW — bypasses routing entirely
        #
        active_workflow = get_active_workflow(request.message_history)
        if active_workflow:
            logger.info(
                "workflow.active",
                extra={"workflow": active_workflow.workflow, "status": active_workflow.status},
            )
            messages = build_messages(
                request=request,
                system_prompt="\n\n".join([load_prompt(brain), load_policy("tone")]),
                workflow_context=self.get_workflow_context(active_workflow),
            )
            response = generate([m.model_dump() for m in messages])
            response.data_used = []
            logger.info(
                "request.complete",
                extra={"path": "active_workflow", "latency_ms": int((perf_counter() - start) * 1000)},
            )
            return response

        #
        # INTENT ROUTER — classifies query before any tools run
        #
        route_result = route(request.query)

        #
        # SOCIAL PATH — no tools, no RAG policy
        #
        if route_result.intent == "social":
            messages = build_messages(
                request=request,
                system_prompt="\n\n".join([load_prompt(brain), load_policy("tone")]),
            )
            response = generate([m.model_dump() for m in messages])
            response.data_used = []
            logger.info(
                "intent",
                extra={"intent": response.intent or "greeting", "reason": response.intent_reason, "tools": []},
            )
            logger.info(
                "request.complete",
                extra={"path": "social", "latency_ms": int((perf_counter() - start) * 1000)},
            )
            return response

        #
        # HANDOFF PATH — no tools, handoff policy only
        #
        if route_result.intent == "handoff":
            messages = build_messages(
                request=request,
                system_prompt="\n\n".join([load_prompt(brain), load_policy("handoff"), load_policy("tone")]),
            )
            response = generate([m.model_dump() for m in messages])
            response.data_used = []
            logger.info(
                "intent",
                extra={"intent": "handoff", "reason": response.intent_reason, "tools": []},
            )
            logger.info(
                "request.complete",
                extra={"path": "handoff", "latency_ms": int((perf_counter() - start) * 1000)},
            )
            return response

        #
        # HOTEL PATH — full tool-use loop
        #
        messages = build_messages(
            request=request,
            system_prompt="\n\n".join([
                load_prompt(brain),
                load_policy("rag"),
                load_policy("handoff"),
                load_policy("tone"),
            ]),
        )

        all_tools = get_tool_definitions(request.brain_id)
        current_input = [m.model_dump() for m in messages]
        tool_call_names: list[str] = []
        ordering_link = None
        catalog_logo: str | None = None
        response = None

        for round_num in range(_MAX_TOOL_ROUNDS):
            called_set = set(tool_call_names)
            tools = [t for t in all_tools if t["name"] not in (called_set & _ONE_SHOT_TOOLS)]

            response, tool_calls = generate_with_tools(current_input, tools)

            if not tool_calls:
                break

            tool_call_names.extend(tc.name for tc in tool_calls)
            logger.info(
                "tools.round",
                extra={"round": round_num + 1, "tools": [tc.name for tc in tool_calls]},
            )

            tool_start = perf_counter()
            tool_outputs, round_link, round_logo = self.tool_executor.execute_tool_calls(tool_calls, request)
            logger.info(
                "tools.executed",
                extra={
                    "tools": [tc.name for tc in tool_calls],
                    "latency_ms": int((perf_counter() - tool_start) * 1000),
                },
            )

            if round_link:
                ordering_link = round_link
            if round_logo:
                catalog_logo = round_logo

            current_input = [
                *current_input,
                *[
                    {
                        "type": "function_call",
                        "id": tc.id,
                        "call_id": tc.call_id,
                        "name": tc.name,
                        "arguments": tc.arguments,
                    }
                    for tc in tool_calls
                ],
                *tool_outputs,
            ]
        else:
            response = generate(current_input)

        logger.info(
            "intent",
            extra={
                "intent": response.intent,
                "reason": response.intent_reason,
                "tools": tool_call_names,
            },
        )

        #
        # POST-PROCESS
        #
        if "get_answers" not in tool_call_names:
            response.data_used = []
        else:
            response.data_used = [item.strip("[]") for item in response.data_used]

        response.service_catalog = None
        if ordering_link and ordering_link.startswith("http"):
            response.service_catalog = ServiceCatalog(
                link=ordering_link,
                message=response.service_catalog_message or "",
                image=catalog_logo or "",
            )

        logger.info(
            "request.complete",
            extra={
                "path": "hotel",
                "tools_called": tool_call_names,
                "latency_ms": int((perf_counter() - start) * 1000),
            },
        )
        return response

    def get_workflow_context(self, workflow_state) -> str:
        if workflow_state.workflow == self.HANDOFF_WORKFLOW:
            return self.get_handoff_active_context(workflow_state.status)

        safe_workflow = re.sub(r"[^a-z0-9_]", "", workflow_state.workflow.lower())[:64]
        safe_status = re.sub(r"[^a-z0-9_]", "", workflow_state.status.lower())[:64]
        return f"Active Workflow:\n\nworkflow={safe_workflow}\nstatus={safe_status}"

    def get_handoff_active_context(self, status: str) -> str:
        return (
            f"Active Workflow:\n\n"
            f"workflow={self.HANDOFF_WORKFLOW}\n"
            f"status={status}\n\n"
            f"The assistant is waiting for confirmation about handing off to a human.\n\n"
            f"Rules:\n"
            f'- If the guest confirms, set is_confirmation=false, handoff=true, workflow_state.workflow="{self.HANDOFF_WORKFLOW}", workflow_state.status="{self.HANDOFF_SUCCESS}".\n'
            f'- If the guest declines, set is_confirmation=false, handoff=false, workflow_state.workflow="{self.HANDOFF_WORKFLOW}", workflow_state.status="{self.HANDOFF_CANCELLED}".\n'
            f'- If the guest is unclear, ask for confirmation again with no follow-up questions, set handoff=false, set is_confirmation=true, and keep workflow_state.status="{self.AWAITING_CONFIRMATION}".'
        )
