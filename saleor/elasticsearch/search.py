from elasticsearch_dsl import DocType, Text, Integer, InnerObjectWrapper, Nested, String, Date
from elasticsearch_dsl import MetaField
from elasticsearch_dsl import Search
from elasticsearch_dsl import analyzer
from elasticsearch_dsl import token_filter
from elasticsearch_dsl.connections import connections

__author__ = 'tkolter'

connections.create_connection()

ngram_analyzer = analyzer(
    'autocomplete_analyzer',
    tokenizer='uax_url_email',
    filter=[
        'lowercase',
        token_filter('autocomplete_filter', type="edgeNGram", min_gram=1, max_gram=20)
    ]
)

lowercase_analyzer = analyzer(
    'lowercase_analyzer',
    tokenizer='lowercase'
)


class Track(InnerObjectWrapper):
    pass


class Release(DocType):
    artist_name = String(search_analyzer=lowercase_analyzer, analyzer=ngram_analyzer, fields={"token": String(analyzer='standard')})
    title = Text(search_analyzer=lowercase_analyzer, analyzer=ngram_analyzer, fields={"token": String(analyzer='standard')})
    released_at = Date()
    description = Text(search_analyzer=lowercase_analyzer, analyzer=ngram_analyzer)
    label = String(search_analyzer=lowercase_analyzer, analyzer=ngram_analyzer, fields={"token": String(analyzer='standard')})

    tracks = Nested({
        'track_pk': Integer(index='not_analyzed'),
        'title': Text(),
        'url': Text(index='not_analyzed')
    })

    class Meta:
        all = MetaField(store=True, analyzer=ngram_analyzer, search_analyzer=lowercase_analyzer)
        index = 'oye'


def search(query, size=10, page=1):
    query_dict = {
        "size": size,
        "from": size * (page-1),
        "sort": [{"released_at": "desc"}],
        "query": {
            "match": {
                "_all": {
                    "query": query,
                    "operator": "and",
                    "fuzziness": "auto",
                    "max_expansions": 10
                }
            }
        },
        "highlight": {
            "fields": {
                "*": {}
            },
            "require_field_match": False
        }
    }

    s = Search().from_dict(query_dict)
    response = s.execute()
    return response
