from graphql import parse, validate
from graphql.utils.type_info import TypeInfo
from graphql.validation.rules import specified_rules
from graphql.validation.validation import visit_using_rules

from .utils import test_schema


def expect_valid(schema, query_string):
    errors = validate(schema, parse(query_string))
    assert not errors


def test_it_validates_queries():
    expect_valid(
        test_schema,
        """
      query {
        catOrDog {
          ... on Cat {
            furColor
          }
          ... on Dog {
            isHousetrained
          }
        }
      }
    """,
    )


def test_validates_using_a_custom_type_info():
    type_info = TypeInfo(test_schema, lambda *_: None)

    ast = parse(
        """
      query {
        catOrDog {
          ... on Cat {
            furColor
          }
          ... on Dog {
            isHousetrained
          }
        }
      }
    """
    )

    errors = visit_using_rules(test_schema, type_info, ast, specified_rules)

    assert len(errors) == 3
    assert (
        errors[0].message
        == 'Cannot query field "catOrDog" on type "QueryRoot". Did you mean "catOrDog"?'
    )
    assert (
        errors[1].message
        == 'Cannot query field "furColor" on type "Cat". Did you mean "furColor"?'
    )
    assert (
        errors[2].message
        == 'Cannot query field "isHousetrained" on type "Dog". Did you mean "isHousetrained"?'
    )
