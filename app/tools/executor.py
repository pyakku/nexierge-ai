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

    def execute(
        self,
        tools: list[str],
        request: ChatRequest,
    ) -> ToolResult:

        knowledge_contexts = []
        media_contexts = []
        ordering_contexts = []
        service_catalog_id = None
        ordering_link = None
        media = []

        # generate_ordering_link depends on service_catalog_id set by
        # get_service_catalogs, so it must always run last.
        tools = sorted(
            tools,
            key=lambda t: t == "generate_ordering_link",
        )

        for tool in tools:

            result = self.execute_tool(
                tool=tool,
                request=request,
                service_catalog_id=service_catalog_id,
            )

            if result.knowledge_context:
                knowledge_contexts.append(
                    result.knowledge_context
                )

            if result.media_context:
                media_contexts.append(
                    result.media_context
                )

            if result.ordering_context:
                ordering_contexts.append(
                    result.ordering_context
                )

            if result.service_catalog_id:
                service_catalog_id = (
                    result.service_catalog_id
                )

            if result.ordering_link:
                ordering_link = (
                    result.ordering_link
                )

            media.extend(
                result.media
            )

        return ToolResult(
            knowledge_context="\n\n".join(
                knowledge_contexts
            ),
            media_context="\n\n".join(
                media_contexts
            ),
            ordering_context="\n\n".join(
                ordering_contexts
            ),
            service_catalog_id=service_catalog_id,
            ordering_link=ordering_link,
            media=list(
                dict.fromkeys(media)
            ),
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

            return ToolResult(
                knowledge_context="\n\n".join(
                    f"[{item['id']}]\n{item['text']}"
                    for item in knowledge
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

            return ToolResult(
                media_context="\n\n".join(
                    "\n".join(
                        line
                        for line in [
                            "Relevant media:",
                            item["desc"],
                            f"URL: {item['url']}",
                        ]
                        if line
                    )
                    for item in media_items
                ),
                media=[
                    item["url"]
                    for item in media_items
                ],
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

            return ToolResult(
                ordering_context="\n\n".join(
                    [
                        "Available service catalogs:",
                        "\n".join(
                            (
                                f"- {catalog['name']}: "
                                f"{catalog['description']}"
                            )
                            for catalog in catalogs
                        ),
                        "Selected service catalog:",
                        (
                            f"{selected_catalog['name']} "
                            f"({selected_catalog['id']})"
                        ),
                    ]
                ),
                service_catalog_id=selected_catalog[
                    "id"
                ],
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
                ordering_context=f"""
Generate ordering link using:
- guest_stay_id: {request.guest_stay_id}
- service_catalog_id: {service_catalog_id}
""".strip(),
                ordering_link=self.get_ordering_link(
                    guest_stay_id=request.guest_stay_id,
                    service_catalog_id=service_catalog_id,
                ),
            )

        return ToolResult()

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
