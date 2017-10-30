import json
from . import newelastic


def test_builds_json_query():
    query = newelastic.build_es_query()
    json.loads(query)
