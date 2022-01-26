from algoliasearch.search_client import SearchClient
from sympy.core.singleton import Singleton


class AlgoliaApiClient(metaclass=Singleton):
    def __init__(self, api_key, app_id, locales):
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
                    ]
                }
            )
