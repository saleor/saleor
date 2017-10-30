from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import MultiMatch

CLIENT = Elasticsearch()


def search(phrase):
    result = (Search()
              .query(MultiMatch(query=phrase, fields=['name', 'description']))
              .using(CLIENT)
              .execute())
    return []


class SearchBackend(object):
    rebuilder_class = None

    def __init__(*args, **kwargs):
        pass

    def search(self, query, model_or_queryset=None):
        pass
