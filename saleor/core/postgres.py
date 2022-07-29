from typing import List, Optional, Union

from django.contrib.postgres.search import (
    CombinedSearchVector,
    SearchVector,
    SearchVectorCombinable,
)
from django.db.models import Expression


class NoValidationSearchVectorCombinable(SearchVectorCombinable):
    def _combine(self, other, connector, reversed):
        if not isinstance(other, NoValidationSearchVectorCombinable):
            raise TypeError(
                "SearchVector can only be combined with other SearchVector "
                "instances, got %s." % type(other).__name__
            )
        if reversed:
            return NoValidationCombinedSearchVector(other, connector, self, self.config)
        return NoValidationCombinedSearchVector(self, connector, other, self.config)


class NoValidationCombinedSearchVector(
    NoValidationSearchVectorCombinable, CombinedSearchVector
):
    contains_aggregate = False
    contains_over_clause = False


class NoValidationSearchVector(SearchVector, NoValidationSearchVectorCombinable):
    """The purpose of this class is to omit Django's SQL compiler's validation.

    This validation can lead to RecursionError while processing a large number of
    expressions.
    If expressions contained aggregate or over clause, then exception still be raised
    during SQL execution instead of before preparing SQL.

    This class is only safe to use with expressions that do not contain aggregation
    and/or over clause.
    """


class FlatSearchVector(Expression):
    """Generate a SQL statements for combined ``SearchVector`` expressions.

    This replaces the logic of Django ORM from recursive ``as_sql()`` and
    ``resolve_expression()``. Allowing to set hundreds of ``SearchVector``.
    """

    function = None
    template = "(%(expressions)s)"
    arg_joiner = "||"

    contains_aggregate = False
    contains_over_clause = False

    def __init__(self, *expressions, output_field=None):
        super().__init__(output_field=output_field)
        self.source_expressions: List[SearchVector] = self._parse_expressions(
            *expressions
        )

    def __repr__(self):
        args = self.arg_joiner.join(str(arg) for arg in self.source_expressions)
        return f"{self.__class__.__name__}({args})"

    def __add__(self, other):
        if not isinstance(other, FlatSearchVector):
            raise TypeError(
                f"Cannot combine FlatSearchVectorCombinable with other "
                f"instances types, got {other!r}."
            )
        return FlatSearchVector(*self.source_expressions + other.source_expressions)

    def get_source_expressions(self):
        return self.source_expressions

    def set_source_expressions(self, exprs):
        self.source_expressions = exprs

    def copy(self):
        copy = super().copy()
        copy.source_expressions = self.source_expressions[:]
        return copy

    def resolve_expression(
        self, query=None, allow_joins=True, reuse=None, summarize=False, for_save=False
    ):
        c = self.copy()
        c.is_summary = summarize
        for pos, arg in enumerate(c.source_expressions):
            c.source_expressions[pos] = arg.resolve_expression(
                query, allow_joins, reuse, summarize, for_save
            )
        return c

    def as_sql(self, compiler, connection, **_extra_context):
        connection.ops.check_expression_support(self)
        sql_parts: List[str] = []
        params: List[Optional[Union[str, int]]] = []
        for arg in self.source_expressions:
            arg_sql, arg_params = compiler.compile(arg)
            sql_parts.append(arg_sql)
            params.extend(arg_params)
        data = {"expressions": self.arg_joiner.join(sql_parts)}
        return self.template % data, params
