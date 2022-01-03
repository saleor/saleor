from algoliasearch.search_client import SearchClient
from sympy.core.singleton import Singleton

from saleor.plugins.algolia.utils import get_locales


class AlgoliaApiClient(metaclass=Singleton):
    def __init__(self, app_id, api_key, *args, **kws):
        super().__init__(*args, **kws)
        self.locales = get_locales()
        self.client = SearchClient.create(app_id=app_id, api_key=api_key)
        self.indices = {
            locale: self.client.init_index(name=f"products_{locale}")
            for locale in self.locales
        }
        for locale, index in self.indices.items():
            index.set_settings(
                settings={
                    "searchableAttributes": [
                        "name",
                        "description",
                    ]
                }
            )

    def list_indexes(self):
        return self.indices
