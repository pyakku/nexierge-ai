from time import perf_counter

from app.brains.router import get_brain_name
from app.core.context_builder import build_context
from app.core.message_builder import build_messages
from app.core.policy_loader import load_policy
from app.core.prompt_loader import load_prompt
from app.models.agent_response import AgentResponse
from app.models.chat_request import ChatRequest
from app.rag.knowledge_service import KnowledgeService
from app.services.response_generator import ResponseGenerator


class Agent:

    def __init__(self):
        self.response_generator = ResponseGenerator()
        self.knowledge_service = KnowledgeService()

    def respond(
        self,
        request: ChatRequest,
    ) -> AgentResponse:

        start = perf_counter()

        brain = get_brain_name(
            request.brain_id
        )

        system_prompt = "\n\n".join(
            [
                load_prompt(brain),
                load_policy("rag"),
            ]
        )

        prompt_time = perf_counter()

        knowledge = self.knowledge_service.retrieve(
            query=request.query,
            hotel_id=request.hotel_id,
            brain_id=request.brain_id,
            sandbox=request.sandbox,
        )

        rag_time = perf_counter()

        context = build_context(
            knowledge
        )

        messages = build_messages(
            request=request,
            system_prompt=system_prompt,
            context=context,
        )

        message_time = perf_counter()

        response = self.response_generator.generate(
            messages
        )

        llm_time = perf_counter()

        print(
            f"Prompt: {(prompt_time - start) * 1000:.0f}ms"
        )

        print(
            f"RAG: {(rag_time - prompt_time) * 1000:.0f}ms"
        )

        print(
            f"Messages: {(message_time - rag_time) * 1000:.0f}ms"
        )

        print(
            f"LLM: {(llm_time - message_time) * 1000:.0f}ms"
        )

        print(
            f"Total: {(llm_time - start) * 1000:.0f}ms"
        )

        return response