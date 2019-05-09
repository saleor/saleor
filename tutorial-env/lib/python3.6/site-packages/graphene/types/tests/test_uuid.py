from ..objecttype import ObjectType
from ..schema import Schema
from ..uuid import UUID


class Query(ObjectType):
    uuid = UUID(input=UUID())

    def resolve_uuid(self, info, input):
        return input


schema = Schema(query=Query)


def test_uuidstring_query():
    uuid_value = "dfeb3bcf-70fd-11e7-a61a-6003088f8204"
    result = schema.execute("""{ uuid(input: "%s") }""" % uuid_value)
    assert not result.errors
    assert result.data == {"uuid": uuid_value}


def test_uuidstring_query_variable():
    uuid_value = "dfeb3bcf-70fd-11e7-a61a-6003088f8204"

    result = schema.execute(
        """query Test($uuid: UUID){ uuid(input: $uuid) }""",
        variable_values={"uuid": uuid_value},
    )
    assert not result.errors
    assert result.data == {"uuid": uuid_value}
