from graphql import Source, parse
from graphql.language.printer import print_ast
from graphql.utils.concat_ast import concat_ast


def test_it_concatenates_two_acts_together():
    source_a = Source("{ a, b, ... Frag }")
    source_b = Source(
        """
        fragment Frag on T {
            c
        }
    """
    )

    ast_a = parse(source_a)
    ast_b = parse(source_b)
    ast_c = concat_ast([ast_a, ast_b])

    assert (
        print_ast(ast_c)
        == """{
  a
  b
  ...Frag
}

fragment Frag on T {
  c
}
"""
    )
