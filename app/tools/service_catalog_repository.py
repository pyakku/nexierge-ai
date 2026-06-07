from app.integrations.xano_client import XanoClient


class ServiceCatalogRepository:

    def __init__(self):
        self.client = XanoClient()

    def get_catalogs(
        self,
        hotel_id: str,
    ) -> list[dict]:

        return self.client.get(
            "service_catalogs/fetch",
            {
                "hotel_id": hotel_id,
            },
        )

    def get_ordering_link(
        self,
        guest_stay_id: str,
        service_catalog_id: str,
    ) -> dict:

        return self.client.get(
            "service_catalogs/ordering_link",
            {
                "guest_stay_id": guest_stay_id,
                "service_catalog_id": service_catalog_id,
            },
        )
