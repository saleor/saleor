
from ..json import JSONString
from ..objecttype import ObjectType
from ..schema import Schema


class Query(ObjectType):
    json = JSONString(input=JSONString())

    def resolve_json(self, info, input):
        return input


schema = Schema(query=Query)


def test_jsonstring_query():
    json_value = '{"key": "value"}'

    json_value_quoted = json_value.replace('"', '\\"')
    result = schema.execute("""{ json(input: "%s") }""" % json_value_quoted)
    assert not result.errors
    assert result.data == {"json": json_value}


def test_jsonstring_query_variable():
    json_value = '{"key": "value"}'

    result = schema.execute(
        """query Test($json: JSONString){ json(input: $json) }""",
        variable_values={"json": json_value},
    )
    assert not result.errors
    assert result.data == {"json": json_value}
