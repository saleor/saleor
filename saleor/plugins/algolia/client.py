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

    def save_object(self, record, locales):
        for locale in locales:
            self.indices[locale].save_object(record)

    def partial_update_object(self, record, locales):
        for locale in locales:
            self.indices[locale].partial_update_object(
                obj=record, request_options={"createIfNotExists": True}
            )

    def delete_object(self, record, locales):
        for locale in locales:
            self.indices[locale].delete_object(record["objectID"])
