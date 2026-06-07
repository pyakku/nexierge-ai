from time import perf_counter

import re

from app.agents.router import Router
from app.brains.router import get_brain_name
from app.core.message_builder import build_messages
from app.core.policy_loader import load_policy
from app.core.prompt_loader import load_prompt
from app.core.workflow_finder import (
    get_active_workflow,
)
from app.models.agent_response import (
    AgentResponse,
    ServiceCatalog,
)
from app.models.chat_request import ChatRequest
from app.services.response_generator import (
    ResponseGenerator,
)
from app.tools.executor import (
    ToolExecutor,
)


class Agent:

    HANDOFF_WORKFLOW = "handoff"
    AWAITING_CONFIRMATION = (
        "awaiting_confirmation"
    )
    HANDOFF_SUCCESS = (
        "handoff_success"
    )
    HANDOFF_CANCELLED = (
        "handoff_cancelled"
    )

    def __init__(self):
        self.router = Router()

        self.response_generator = (
            ResponseGenerator()
        )

        self.tool_executor = (
            ToolExecutor()
        )

    def respond(
        self,
        request: ChatRequest,
    ) -> AgentResponse:

        start = perf_counter()

        #
        # ACTIVE WORKFLOW
        #
        active_workflow = (
            get_active_workflow(
                request.message_history
            )
        )

        if active_workflow:

            print(
                "\n=== ACTIVE WORKFLOW ==="
            )

            print(active_workflow)

            brain = get_brain_name(
                request.brain_id
            )

            messages = build_messages(
                request=request,
                system_prompt=load_prompt(
                    brain
                ),
                workflow_context=(
                    self.get_workflow_context(
                        active_workflow
                    )
                ),
            )

            response = (
                self.response_generator.generate(
                    messages
                )
            )

            response.data_used = []

            return response

        #
        # ROUTER
        #
        decision = self.router.route(
            request.query,
            request.brain_id,
        )

        router_time = perf_counter()

        print("\n=== ROUTER ===")
        print(decision)

        #
        # TOOL EXECUTION
        #
        knowledge_context = ""
        media_context = ""
        ordering_context = ""
        workflow_context = ""
        ordering_link = None
        media = []

        if decision.intent == "HANDOFF":
            workflow_context = (
                self.get_handoff_start_context()
            )

        if decision.tools:

            tool_start = (
                perf_counter()
            )

            tool_result = (
                self.tool_executor.execute(
                    tools=decision.tools,
                    request=request,
                )
            )

            knowledge_context = (
                tool_result.knowledge_context
            )
            media_context = (
                tool_result.media_context
            )
            ordering_context = (
                tool_result.ordering_context
            )
            ordering_link = (
                tool_result.ordering_link
            )
            media = tool_result.media

            tool_time = (
                perf_counter()
            )

            print(
                f"Tool ({decision.tools}): "
                f"{(tool_time - tool_start) * 1000:.0f}ms"
            )

        #
        # BRAIN
        #
        brain = get_brain_name(
            request.brain_id
        )

        messages = build_messages(
            request=request,
            system_prompt="\n\n".join(
                [
                    load_prompt(brain),
                    load_policy("rag"),
                ]
            ),
            knowledge_context=knowledge_context,
            media_context=media_context,
            ordering_context=ordering_context,
            workflow_context=workflow_context,
        )

        message_time = (
            perf_counter()
        )

        response = (
            self.response_generator.generate(
                messages
            )
        )

        if "get_answers" not in decision.tools:
            response.data_used = []

        if ordering_link:
            response.service_catalog = (
                ServiceCatalog(
                    link=ordering_link,
                    message="",
                    image="",
                )
            )

        if media:
            response.media = list(
                dict.fromkeys(
                    [
                        *response.media,
                        *media,
                    ]
                )
            )

        llm_time = (
            perf_counter()
        )

        print(
            f"Router: {(router_time - start) * 1000:.0f}ms"
        )

        print(
            f"Messages: {(message_time - router_time) * 1000:.0f}ms"
        )

        print(
            f"LLM: {(llm_time - message_time) * 1000:.0f}ms"
        )

        print(
            f"Total: {(llm_time - start) * 1000:.0f}ms"
        )

        return response

    def get_workflow_context(
        self,
        workflow_state,
    ) -> str:

        if (
            workflow_state.workflow
            == self.HANDOFF_WORKFLOW
        ):
            return self.get_handoff_active_context(
                workflow_state.status
            )

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

    def get_handoff_start_context(
        self,
    ) -> str:

        return f"""
Workflow Instruction:

The guest asked for a human handoff.
Ask only for confirmation.
Do not ask any follow-up questions about the issue.

Required output:
- is_confirmation=true
- handoff=false
- workflow_state.workflow="{self.HANDOFF_WORKFLOW}"
- workflow_state.status="{self.AWAITING_CONFIRMATION}"
""".strip()

    def get_handoff_active_context(
        self,
        status: str,
    ) -> str:

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
