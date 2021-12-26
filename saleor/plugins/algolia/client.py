from algoliasearch.search_client import SearchClient
from sympy.core.singleton import Singleton


class AlgoliaApiClient(metaclass=Singleton):
    def __init__(self, app_id, api_key, locales, *args, **kws):
        super().__init__(*args, **kws)
        self.client = SearchClient.create(app_id=app_id, api_key=api_key)
        self.indices = {
            locale: self.client.init_index(name=f"products_{locale}")
            for locale in locales
        }
        for locale, index in self.indices.items():
            index.set_settings(
                settings={
                    "searchableAttributes": [
                        "sku",
                        "name",
                        "channels",
                        "description",
                        "translation",
                    ]
                }
            )

    def list_indexes(self):
        return self.indices

    def save_object(self, record, locales):
        for locale in locales:
            self.indices[locale].save_object(record)

    def delete_record(self, record, locales):
        for locale in locales:
            self.indices[locale].delete_object(record["objectID"])
