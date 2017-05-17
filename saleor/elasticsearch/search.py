from constance import config
from elasticsearch_dsl import DocType, Text, Integer, InnerObjectWrapper, Nested, String, Date
from elasticsearch_dsl import Keyword
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
    tokenizer='standard',
    filter=[
        'lowercase'
    ]
)


class Track(InnerObjectWrapper):
    pass


class Release(DocType):
    artist_name = String(
        search_analyzer=lowercase_analyzer,
        analyzer=lowercase_analyzer,
        fields={'raw': Keyword()})
    title = Text(search_analyzer=lowercase_analyzer, analyzer=lowercase_analyzer)
    released_at = Date()
    description = Text(search_analyzer=lowercase_analyzer, analyzer=lowercase_analyzer)
    label = String(
        search_analyzer=lowercase_analyzer,
        analyzer=lowercase_analyzer,
        fields={'raw': Keyword()}
    )

    tracks = Nested({
        'track_pk': Integer(index='not_analyzed'),
        'title': Text(),
        'url': Text(index='not_analyzed')
    })

    class Meta:
        all = MetaField(store=True, analyzer=lowercase_analyzer, search_analyzer=lowercase_analyzer)
        index = 'oye'


class Artist(DocType):
    name = String(
        search_analyzer=lowercase_analyzer,
        analyzer=lowercase_analyzer
    )

    class Meta:
        index = 'oye'


QUERY_FIELDS = [
    'title.token',
    'artist_name',
    'description',
    'label',
    # 'name',
    '_all',
]


def search(query, size=10, page=1, doc_type=None, fields=QUERY_FIELDS):
    should_queries = []
    should_queries.extend(
        [
            {
                "match_phrase": {
                    field: {
                        "query": query,
                        "analyzer": "standard"
                    }
                }
            }
            for field in fields
        ]
    )

    should_queries.extend(
        [
            {
                "match": {
                    field: {
                        "query": query,
                        "fuzziness":  config.SEARCH_FUZZINESS,
                        # "operator": "or",
                        "operator": "and",
                        "prefix_length": config.SEARCH_PREFIX_LENGTH,
                        "max_expansions": 10,
                        # "analyzer": "standard"
                     }
                 }
            }
            for field in fields
        ]
    )

    query_dict = {
        "size": size,
        "from": size * (page - 1),
        "sort": [
            # {"_script": {
            #     "type": "number",
            #     "order": "desc",
            #     "script": {
            #         "lang": "painless",
            #         "inline": "def sf = new SimpleDateFormat(\"yyyy-MM-dd\"); if (doc['released_at'].value > sf.parse('2016-11-06').getTime()) 1; else 0"
            #     }
            # }},
            # {
            #     "_script": {
            #         "type": "string",
            #         "order": "desc",
            #         "script": {
            #             "lang": "painless",
            #             "inline": "if (doc['_type'].value == 'artist') 1; else 0;"
            #         }
            #     }
            # },
            {"released_at": "desc"},
            {"_score": "desc"}
        ],
        "query": {
            "bool": {
                "should": should_queries
            }
        # },
        # "highlight": {
        #     "fields": {
        #         "*": {}
        #     },
        #     "require_field_match": False
        }
    }

    s = Search().from_dict(query_dict).doc_type(doc_type)
    response = s.execute()
    return response
