from ...language.base import parse
from ...utils.ast_to_code import ast_to_code
from ..compiled import GraphQLCompiledDocument
from .schema import schema


def test_compileddocument_from_module_dict():
    # type: () -> None
    document_string = "{ hello }"
    document_ast = parse(document_string)
    document = GraphQLCompiledDocument.from_module_dict(
        schema,
        {
            "document_string": document_string,
            "document_ast": document_ast,
            "execute": lambda *_: True,
        },
    )
    assert document.operations_map == {None: "query"}
    assert document.document_string == document_string
    assert document.document_ast == document_ast
    assert document.schema == schema
    assert document.execute()


def test_compileddocument_from_code():
    # type: () -> None
    document_string = "{ hello }"
    document_ast = parse(document_string)
    code = '''
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from graphql.language import ast
from graphql.language.parser import Loc
from graphql.language.source import Source


schema = None
document_string = """{document_string}"""
source = Source(document_string)


def loc(start, end):
    return Loc(start, end, source)

document_ast = {document_ast}

def execute(*_):
    return True
'''.format(
        document_string=document_string, document_ast=ast_to_code(document_ast)
    )
    document = GraphQLCompiledDocument.from_code(schema, code)
    assert document.operations_map == {None: "query"}
    assert document.document_string == document_string
    assert document.document_ast == document_ast
    assert document.schema == schema
    assert document.execute()
