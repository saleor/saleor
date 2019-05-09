"""
This module implements the functionality to take any Python expression as a
string and fix all numbers and other things before evaluating it,
thus

1/2

returns

Integer(1)/Integer(2)

We use the Python ast module for that, which is in python2.6 and later. It is
well documented at docs.python.org.

Some tips to understand how this works: use dump() to get a nice
representation of any node. Then write a string of what you want to get,
e.g. "Integer(1)", parse it, dump it and you'll see that you need to do
"Call(Name('Integer', Load()), [node], [], None, None)". You don't need
to bother with lineno and col_offset, just call fix_missing_locations()
before returning the node.
"""

from __future__ import print_function, division

from sympy.core.basic import Basic
from sympy.core.compatibility import exec_
from sympy.core.sympify import SympifyError

from ast import parse, NodeTransformer, Call, Name, Load, \
    fix_missing_locations, Str, Tuple

class Transform(NodeTransformer):

    def __init__(self, local_dict, global_dict):
        NodeTransformer.__init__(self)
        self.local_dict = local_dict
        self.global_dict = global_dict

    def visit_Num(self, node):
        if isinstance(node.n, int):
            return fix_missing_locations(Call(Name('Integer', Load()),
                    [node], [], None, None))
        elif isinstance(node.n, float):
            return fix_missing_locations(Call(Name('Float', Load()),
                [node], [], None, None))
        return node

    def visit_Name(self, node):
        if node.id in self.local_dict:
            return node
        elif node.id in self.global_dict:
            name_obj = self.global_dict[node.id]

            if isinstance(name_obj, (Basic, type)) or callable(name_obj):
                return node
        elif node.id in ['True', 'False']:
            return node
        return fix_missing_locations(Call(Name('Symbol', Load()),
                [Str(node.id)], [], None, None))

    def visit_Lambda(self, node):
        args = [self.visit(arg) for arg in node.args.args]
        body = self.visit(node.body)
        n = Call(Name('Lambda', Load()),
            [Tuple(args, Load()), body], [], None, None)
        return fix_missing_locations(n)

def parse_expr(s, local_dict):
    """
    Converts the string "s" to a SymPy expression, in local_dict.

    It converts all numbers to Integers before feeding it to Python and
    automatically creates Symbols.
    """
    global_dict = {}
    exec_('from sympy import *', global_dict)
    try:
        a = parse(s.strip(), mode="eval")
    except SyntaxError:
        raise SympifyError("Cannot parse %s." % repr(s))
    a = Transform(local_dict, global_dict).visit(a)
    e = compile(a, "<string>", "eval")
    return eval(e, global_dict, local_dict)
