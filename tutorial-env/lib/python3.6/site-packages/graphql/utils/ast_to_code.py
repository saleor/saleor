from ..language.ast import Node
from ..language.parser import Loc

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any


def ast_to_code(ast, indent=0):
    # type: (Any, int) -> str
    """
    Converts an ast into a python code representation of the AST.
    """
    code = []

    def append(line):
        # type: (str) -> None
        code.append(("    " * indent) + line)

    if isinstance(ast, Node):
        append("ast.{}(".format(ast.__class__.__name__))
        indent += 1
        for i, k in enumerate(ast._fields, 1):
            v = getattr(ast, k)
            append("{}={},".format(k, ast_to_code(v, indent)))
        if ast.loc:
            append("loc={}".format(ast_to_code(ast.loc, indent)))

        indent -= 1
        append(")")

    elif isinstance(ast, Loc):
        append("loc({}, {})".format(ast.start, ast.end))

    elif isinstance(ast, list):
        if ast:
            append("[")
            indent += 1

            for i, it in enumerate(ast, 1):
                is_last = i == len(ast)
                append(ast_to_code(it, indent) + ("," if not is_last else ""))

            indent -= 1
            append("]")
        else:
            append("[]")

    else:
        append(repr(ast))

    return "\n".join(code).strip()
