from app.rag.knowledge_service import (
    KnowledgeService,
)


class SearchKnowledgeTool:

    def __init__(self):
        self.service = KnowledgeService()

    def execute(
        self,
        query,
        hotel_id,
        brain_id,
        sandbox,
    ):

        return self.service.retrieve(
            query=query,
            hotel_id=hotel_id,
            brain_id=brain_id,
            sandbox=sandbox,
        )