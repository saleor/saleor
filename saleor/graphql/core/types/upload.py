import graphene


class Upload(graphene.types.Scalar):

    class Meta:
        description = '''Variables of this type must be set to null in
        mutations. They will be replaced with a filename from a following
        multipart part containing a binary file. See:
        https://github.com/jaydenseric/graphql-multipart-request-spec'''

    @staticmethod
    def serialize(value):
        return value

    @staticmethod
    def parse_literal(node):
        return node

    @staticmethod
    def parse_value(value):
        return value
