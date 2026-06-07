import logging
import re
from time import perf_counter

from app.brains.router import get_brain_name
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


class Agent:

    HANDOFF_WORKFLOW = "handoff"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    HANDOFF_SUCCESS = "handoff_success"
    HANDOFF_CANCELLED = "handoff_cancelled"

    def __init__(self):
        self.tool_executor = ToolExecutor()

    def respond(
        self,
        request: ChatRequest,
    ) -> AgentResponse:

        start = perf_counter()

        #
        # ACTIVE WORKFLOW — bypasses tool-use entirely
        #
        active_workflow = get_active_workflow(request.message_history)

        if active_workflow:
            logger.info(
                "workflow.active",
                extra={
                    "workflow": active_workflow.workflow,
                    "status": active_workflow.status,
                },
            )

            brain = get_brain_name(request.brain_id)
            messages = build_messages(
                request=request,
                system_prompt="\n\n".join([
                    load_prompt(brain),
                    load_policy("tone"),
                ]),
                workflow_context=self.get_workflow_context(active_workflow),
            )

            response = generate([m.model_dump() for m in messages])
            response.data_used = []

            logger.info(
                "request.complete",
                extra={
                    "path": "active_workflow",
                    "latency_ms": int((perf_counter() - start) * 1000),
                },
            )
            return response

        #
        # MAIN PATH — single LLM with tool-use
        #
        brain = get_brain_name(request.brain_id)
        messages = build_messages(
            request=request,
            system_prompt="\n\n".join([
                load_prompt(brain),
                load_policy("rag"),
                load_policy("handoff"),
                load_policy("tone"),
            ]),
        )

        tools = get_tool_definitions(request.brain_id)
        current_input = [m.model_dump() for m in messages]
        tool_call_names: list[str] = []
        ordering_link = None
        catalog_logo: str | None = None
        response = None

        #
        # TOOL-USE LOOP
        #
        first_round = True
        for round_num in range(_MAX_TOOL_ROUNDS):

            response, tool_calls = generate_with_tools(current_input, tools)

            if first_round:
                first_round = False
                logger.info(
                    "intent",
                    extra={
                        "intent": response.intent if response else None,
                        "reason": response.intent_reason if response else None,
                        "tools_called": [tc.name for tc in tool_calls],
                    },
                )

            if not tool_calls:
                break

            tool_call_names.extend(tc.name for tc in tool_calls)
            logger.info(
                "tools.round",
                extra={
                    "round": round_num + 1,
                    "tools": [tc.name for tc in tool_calls],
                },
            )

            tool_start = perf_counter()
            tool_outputs, round_link, round_logo = (
                self.tool_executor.execute_tool_calls(tool_calls, request)
            )
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
            # Exhausted rounds without a direct response — force final call without tools
            response = generate(current_input)

        #
        # POST-PROCESS
        #
        if "get_answers" not in tool_call_names:
            response.data_used = []
        else:
            response.data_used = [
                item.strip("[]") for item in response.data_used
            ]

        if ordering_link:
            response.service_catalog = ServiceCatalog(
                link=ordering_link,
                message=response.service_catalog_message or "",
                image=catalog_logo or "",
            )


        logger.info(
            "request.complete",
            extra={
                "path": "tool_use",
                "tools_called": tool_call_names,
                "latency_ms": int((perf_counter() - start) * 1000),
            },
        )

        return response

    def get_workflow_context(self, workflow_state) -> str:

        if workflow_state.workflow == self.HANDOFF_WORKFLOW:
            return self.get_handoff_active_context(workflow_state.status)

        safe_workflow = re.sub(
            r"[^a-z0-9_]", "", workflow_state.workflow.lower()
        )[:64]
        safe_status = re.sub(
            r"[^a-z0-9_]", "", workflow_state.status.lower()
        )[:64]

        return f"""
Active Workflow:

workflow={safe_workflow}
status={safe_status}
""".strip()

    def get_handoff_active_context(self, status: str) -> str:

        return f"""
Active Workflow:

workflow={self.HANDOFF_WORKFLOW}
status={status}

The assistant is waiting for confirmation about handing off to a human.

Rules:
- If the guest confirms, set is_confirmation=false, handoff=true, workflow_state.workflow="{self.HANDOFF_WORKFLOW}", workflow_state.status="{self.HANDOFF_SUCCESS}".
- If the guest declines, set is_confirmation=false, handoff=false, workflow_state.workflow="{self.HANDOFF_WORKFLOW}", workflow_state.status="{self.HANDOFF_CANCELLED}".
- If the guest is unclear, ask for confirmation again with no follow-up questions, set handoff=false, set is_confirmation=true, and keep workflow_state.status="{self.AWAITING_CONFIRMATION}".
""".strip()
