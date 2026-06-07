import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter

from app.models.chat_request import (
    ChatRequest,
)
from app.models.brain import Brain
from app.models.tool_result import (
    ToolResult,
)
from app.rag.media_retriever import (
    MediaRetriever,
)
from app.rag.knowledge_service import (
    KnowledgeService,
)
from app.tools.service_catalog_repository import (
    ServiceCatalogRepository,
)


logger = logging.getLogger(__name__)


class ToolExecutor:

    def __init__(self):
        self.knowledge_service = (
            KnowledgeService()
        )
        self.media_retriever = (
            MediaRetriever()
        )
        self.service_catalog_repository = (
            ServiceCatalogRepository()
        )

    # Tools that must run after all others (depend on prior results).
    _RUNS_LAST = {"generate_ordering_link"}

    def execute(
        self,
        tools: list[str],
        request: ChatRequest,
    ) -> ToolResult:

        independent = [
            t for t in tools if t not in self._RUNS_LAST
        ]
        dependent = [
            t for t in tools if t in self._RUNS_LAST
        ]

        knowledge_contexts = []
        media_contexts = []
        ordering_contexts = []
        service_catalog_id = None
        ordering_link = None
        media = []

        def collect(result: ToolResult) -> None:
            nonlocal service_catalog_id, ordering_link
            if result.knowledge_context:
                knowledge_contexts.append(result.knowledge_context)
            if result.media_context:
                media_contexts.append(result.media_context)
            if result.ordering_context:
                ordering_contexts.append(result.ordering_context)
            if result.service_catalog_id:
                service_catalog_id = result.service_catalog_id
            if result.ordering_link:
                ordering_link = result.ordering_link
            media.extend(result.media)

        if len(independent) > 1:
            with ThreadPoolExecutor() as pool:
                futures = {
                    pool.submit(
                        self.execute_tool, tool, request, None
                    ): tool
                    for tool in independent
                }
                for future in as_completed(futures):
                    collect(future.result())
        elif independent:
            collect(
                self.execute_tool(independent[0], request, None)
            )

        for tool in dependent:
            collect(
                self.execute_tool(tool, request, service_catalog_id)
            )

        return ToolResult(
            knowledge_context="\n\n".join(knowledge_contexts),
            media_context="\n\n".join(media_contexts),
            ordering_context="\n\n".join(ordering_contexts),
            service_catalog_id=service_catalog_id,
            ordering_link=ordering_link,
            media=list(dict.fromkeys(media)),
        )

    def execute_tool(
        self,
        tool: str,
        request: ChatRequest,
        service_catalog_id: str | None = None,
    ) -> ToolResult:

        #
        # RAG
        #
        if tool == "get_answers":

            knowledge = (
                self.knowledge_service.retrieve(
                    query=request.query,
                    hotel_id=request.hotel_id,
                    brain_id=request.brain_id,
                    sandbox=request.sandbox,
                )
            )

            if not knowledge:
                return ToolResult(knowledge_context="No relevant knowledge base items found.")

            items_text = "\n\n".join(
                f"[{item['id']}]\n{item['text']}"
                for item in knowledge
            )
            return ToolResult(
                knowledge_context=(
                    "Knowledge Base Results:\n"
                    "Use these items to answer the guest. "
                    "Add each item's ID (the value in square brackets) to data_used if you reference it.\n\n"
                    + items_text
                )
            )
        #
        # MEDIA
        #
        if tool == "get_media":

            media_items = (
                self.media_retriever.retrieve(
                    query=request.query,
                    hotel_id=request.hotel_id,
                    brain_id=request.brain_id,
                    sandbox=request.sandbox,
                )
            )

            if not media_items:
                return ToolResult()

            logger.debug(
                "media.results",
                extra={"items": [{"desc": i.get("desc", ""), "url": i["url"]} for i in media_items]},
            )

            items_text = "\n\n".join(
                f"desc: {item.get('desc', '')}\nurl: {item['url']}"
                for item in media_items
            )
            return ToolResult(
                media_context=(
                    "Relevant media:\n\n"
                    + items_text
                    + "\n\nFor each relevant item, include its url in the media array of your response."
                ),
                media=[item["url"] for item in media_items],
            )

    
        
        # ROOM DETAILS
        #
        if tool == "room_details":

            return ToolResult(
                knowledge_context=(
                    "Room details are not available at this time."
                )
            )

        #
        # SERVICE CATALOGS
        #
        if tool == "get_service_catalogs":

            catalogs = (
                self.service_catalog_repository.get_catalogs(
                    request.hotel_id
                )
            )

            selected_catalog = (
                self.select_service_catalog(
                    query=request.query,
                    catalogs=catalogs,
                )
            )

            if not selected_catalog:
                return ToolResult()

            logo = (selected_catalog.get("logo") or {}).get("url") or ""

            return ToolResult(
                ordering_context="\n\n".join(
                    [
                        "Available service catalogs:",
                        "\n".join(
                            f"- {catalog['name']}: {catalog['description']}"
                            for catalog in catalogs
                        ),
                        "Selected service catalog:",
                        f"{selected_catalog['name']} ({selected_catalog['id']})",
                    ]
                ),
                service_catalog_id=selected_catalog["id"],
                catalog_logo=logo,
            )

        #
        # ORDERING LINK
        #
        if tool == "generate_ordering_link":

            if (
                request.brain_id
                != Brain.GUEST_IN_STAY
            ):
                return ToolResult()

            if (
                not request.guest_stay_id
                or not service_catalog_id
            ):
                return ToolResult()

            return ToolResult(
                ordering_context=(
                    f"Ordering link generated for guest_stay_id={request.guest_stay_id}.\n"
                    "Populate service_catalog_message with a short, natural message inviting the guest to use the link."
                ),
                ordering_link=self.get_ordering_link(
                    guest_stay_id=request.guest_stay_id,
                    service_catalog_id=service_catalog_id,
                ),
            )

        return ToolResult()

    def execute_tool_calls(
        self,
        tool_calls: list,
        request: ChatRequest,
    ) -> tuple[list[dict], str | None, list[str], str | None]:
        """
        Execute tool calls from the LLM (tool-use flow).

        Returns:
            tool_outputs: function_call_output dicts for the next LLM input
            ordering_link: populated if generate_ordering_link ran
            media: collected media URLs
            catalog_logo: logo URL from get_service_catalogs
        """
        tool_outputs = []
        ordering_link = None
        media = []
        catalog_id: str | None = None
        catalog_logo: str | None = None

        for tc in tool_calls:
            try:
                args = json.loads(tc.arguments) if tc.arguments else {}
            except (json.JSONDecodeError, ValueError):
                args = {}

            # generate_ordering_link passes service_catalog_id as an argument
            service_catalog_id = args.get("service_catalog_id") or catalog_id

            tool_start = perf_counter()
            result = self.execute_tool(
                tool=tc.name,
                request=request,
                service_catalog_id=service_catalog_id,
            )
            logger.debug(
                "tool.executed",
                extra={
                    "tool": tc.name,
                    "latency_ms": int((perf_counter() - tool_start) * 1000),
                },
            )

            if result.service_catalog_id:
                catalog_id = result.service_catalog_id
            if result.ordering_link:
                ordering_link = result.ordering_link
            if result.catalog_logo:
                catalog_logo = result.catalog_logo
            media.extend(result.media)

            parts = [
                p for p in [
                    result.knowledge_context,
                    result.media_context,
                    result.ordering_context,
                ]
                if p
            ]

            tool_outputs.append({
                "type": "function_call_output",
                "call_id": tc.call_id,
                "output": "\n\n".join(parts) if parts else "Done.",
            })

        return tool_outputs, ordering_link, list(dict.fromkeys(media)), catalog_logo

    def select_service_catalog(
        self,
        query: str,
        catalogs: list[dict],
    ) -> dict | None:

        if not catalogs:
            return None

        query_tokens = set(
            self.tokenize(query)
        )

        best_catalog = None
        best_score = -1

        for catalog in catalogs:

            haystack = " ".join(
                [
                    catalog.get("name", ""),
                    catalog.get(
                        "description", ""
                    ),
                ]
            )

            catalog_tokens = set(
                self.tokenize(haystack)
            )

            score = len(
                query_tokens
                & catalog_tokens
            )

            if catalog.get(
                "name", ""
            ).lower() in query.lower():
                score += 3

            if score > best_score:
                best_score = score
                best_catalog = catalog

        return best_catalog or catalogs[0]

    def tokenize(
        self,
        text: str,
    ) -> list[str]:

        return [
            token
            for token in "".join(
                char.lower()
                if char.isalnum()
                else " "
                for char in text
            ).split()
            if token
        ]

    def get_ordering_link(
        self,
        guest_stay_id: str,
        service_catalog_id: str,
    ) -> str | None:

        response = (
            self.service_catalog_repository.get_ordering_link(
                guest_stay_id=guest_stay_id,
                service_catalog_id=service_catalog_id,
            )
        )

        return response.get("url")
