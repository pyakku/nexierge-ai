from app.integrations.xano_client import XanoClient


class KnowledgeRepository:

    def __init__(self):
        self.client = XanoClient()

    def get_by_ids(
        self,
        ids: list[str],
    ):

        return self.client.post(
            "knowledge_unit/bulk",
            {
                "ids": ids
            }
        )