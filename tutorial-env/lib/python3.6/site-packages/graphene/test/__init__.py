from promise import Promise, is_thenable
import six
from graphql.error import format_error as format_graphql_error
from graphql.error import GraphQLError

from graphene.types.schema import Schema


def default_format_error(error):
    if isinstance(error, GraphQLError):
        return format_graphql_error(error)

    return {"message": six.text_type(error)}


def format_execution_result(execution_result, format_error):
    if execution_result:
        response = {}

        if execution_result.errors:
            response["errors"] = [format_error(e) for e in execution_result.errors]

        if not execution_result.invalid:
            response["data"] = execution_result.data

        return response


class Client(object):
    def __init__(self, schema, format_error=None, **execute_options):
        assert isinstance(schema, Schema)
        self.schema = schema
        self.execute_options = execute_options
        self.format_error = format_error or default_format_error

    def format_result(self, result):
        return format_execution_result(result, self.format_error)

    def execute(self, *args, **kwargs):
        executed = self.schema.execute(*args, **dict(self.execute_options, **kwargs))
        if is_thenable(executed):
            return Promise.resolve(executed).then(self.format_result)

        return self.format_result(executed)
