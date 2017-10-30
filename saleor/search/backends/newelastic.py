import json


def build_es_query():
    return json.dumps({})


class SearchBackend(object):
    rebuilder_class = None

    def __init__(*args, **kwargs):
        pass

    def search(self, query, model_or_queryset):
        return []
