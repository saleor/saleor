from typing import List

from algoliasearch.search_client import SearchClient

from saleor.plugins.algolia.utils import SingletonMeta


class AlgoliaApiClient(metaclass=SingletonMeta):
    def __init__(self, api_key: str, app_id: str, locales: List[str]) -> None:
        self.client = SearchClient.create(app_id=app_id, api_key=api_key)
        self.indices = {
            locale: self.client.init_index(name=f"products_{locale}")
            for locale in locales
        }
        for locale, index in self.indices.items():
            index.set_settings(
                settings={
                    "searchableAttributes": [
                        "skus",
                        "name",
                        "description",
                    ],
                    "replicas": [
                        f"{index.name}.price_asc",
                        f"{index.name}.price_desc",
                        f"{index.name}.popularity_desc",
                        f"{index.name}.publication_date_desc",
                    ],
                    "customRanking": [f"asc({index.name}.default-channel.price)"],
                }
            )
