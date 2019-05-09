from .execution import ExecutionResult
from .backend import get_default_backend

from promise import promisify

# Necessary for static type checking
if False:  # flake8: noqa
    from promise import Promise
    from rx import Observable
    from typing import Any, Union, Optional
    from .language.ast import Document
    from .type.schema import GraphQLSchema

# This is the primary entry point function for fulfilling GraphQL operations
# by parsing, validating, and executing a GraphQL document along side a
# GraphQL schema.

# More sophisticated GraphQL servers, such as those which persist queries,
# may wish to separate the validation and execution phases to a static time
# tooling step, and a server runtime step.

# schema:
#    The GraphQL type system to use when validating and executing a query.
# requestString:
#    A GraphQL language formatted string representing the requested operation.
# rootValue:
#    The value provided as the first argument to resolver functions on the top
#    level type (e.g. the query object type).
# variableValues:
#    A mapping of variable name to runtime value to use for all variables
#    defined in the requestString.
# operationName:
#    The name of the operation to use if requestString contains multiple
#    possible operations. Can be omitted if requestString contains only
#    one operation.


def graphql(*args, **kwargs):
    # type: (*Any, **Any) -> Union[ExecutionResult, Observable, Promise[ExecutionResult]]
    return_promise = kwargs.get("return_promise", False)
    if return_promise:
        return execute_graphql_as_promise(*args, **kwargs)
    else:
        return execute_graphql(*args, **kwargs)


def execute_graphql(
    schema,  # type: GraphQLSchema
    request_string="",  # type: Union[Document, str]
    root=None,  # type: Any
    context=None,  # type: Optional[Any]
    variables=None,  # type: Optional[Any]
    operation_name=None,  # type: Optional[Any]
    middleware=None,  # type: Optional[Any]
    backend=None,  # type: Optional[Any]
    **execute_options  # type: Any
):
    # type: (...) -> Union[ExecutionResult, Observable, Promise[ExecutionResult]]
    try:
        if backend is None:
            backend = get_default_backend()

        document = backend.document_from_string(schema, request_string)
        return document.execute(
            root=root,
            context=context,
            operation_name=operation_name,
            variables=variables,
            middleware=middleware,
            **execute_options
        )
    except Exception as e:
        return ExecutionResult(errors=[e], invalid=True)


@promisify
def execute_graphql_as_promise(*args, **kwargs):
    return execute_graphql(*args, **kwargs)
