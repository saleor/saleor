""" Optimizations of the expression tree representation for better CSE
opportunities.
"""
from __future__ import print_function, division

from sympy.core import Add, Basic, Mul
from sympy.core.basic import preorder_traversal
from sympy.core.singleton import S
from sympy.utilities.iterables import default_sort_key


def sub_pre(e):
    """ Replace y - x with -(x - y) if -1 can be extracted from y - x.
    """
    reps = [a for a in e.atoms(Add) if a.could_extract_minus_sign()]

    # make it canonical
    reps.sort(key=default_sort_key)

    e = e.xreplace(dict((a, Mul._from_args([S.NegativeOne, -a])) for a in reps))
    # repeat again for persisting Adds but mark these with a leading 1, -1
    # e.g. y - x -> 1*-1*(x - y)
    if isinstance(e, Basic):
        negs = {}
        for a in sorted(e.atoms(Add), key=default_sort_key):
            if a in reps or a.could_extract_minus_sign():
                negs[a] = Mul._from_args([S.One, S.NegativeOne, -a])
        e = e.xreplace(negs)
    return e


def sub_post(e):
    """ Replace 1*-1*x with -x.
    """
    replacements = []
    for node in preorder_traversal(e):
        if isinstance(node, Mul) and \
            node.args[0] is S.One and node.args[1] is S.NegativeOne:
            replacements.append((node, -Mul._from_args(node.args[2:])))
    for node, replacement in replacements:
        e = e.xreplace({node: replacement})

    return e
