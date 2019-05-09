# https://github.com/graphql-python/graphene/issues/720
# InputObjectTypes overwrite the "fields" attribute of the provided
# _meta object, so even if dynamic fields are provided with a standard
# InputObjectTypeOptions, they are ignored.

import graphene


class MyInputClass(graphene.InputObjectType):
    @classmethod
    def __init_subclass_with_meta__(
        cls, container=None, _meta=None, fields=None, **options
    ):
        if _meta is None:
            _meta = graphene.types.inputobjecttype.InputObjectTypeOptions(cls)
        _meta.fields = fields
        super(MyInputClass, cls).__init_subclass_with_meta__(
            container=container, _meta=_meta, **options
        )


class MyInput(MyInputClass):
    class Meta:
        fields = dict(x=graphene.Field(graphene.Int))


class Query(graphene.ObjectType):
    myField = graphene.Field(graphene.String, input=graphene.Argument(MyInput))

    def resolve_myField(parent, info, input):
        return "ok"


def test_issue():
    query_string = """
    query myQuery {
      myField(input: {x: 1})
    }
    """

    schema = graphene.Schema(query=Query)
    result = schema.execute(query_string)

    assert not result.errors
