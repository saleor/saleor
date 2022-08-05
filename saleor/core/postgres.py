import logging
from typing import List, Optional, Union

from django.conf import settings
from django.contrib.postgres.search import (
    CombinedSearchVector,
    SearchVector,
    SearchVectorCombinable,
)
from django.db.models import Expression

logger = logging.getLogger(__name__)


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


class FlatConcat(Expression):
    """Generate a SQL statements for expressions to be concatenated.

    This replaces the logic of Django ORM from recursive ``as_sql()`` and
    ``resolve_expression()`` from some functions such as ``SearchVector``.

    The function ``django.db.models.functions.text.Concat`` is recursive thus
    will crash when setting hundreds of expressions to be concatenated.
    """

    function = None
    template = "(%(expressions)s)"
    arg_joiner = "||"

    contains_aggregate = False
    contains_over_clause = False

    # Maximum allowed expression to be passed to the function
    # If ``silent_drop_expression`` is True then it will truncate
    # and log a warning event. Otherwise, it will raise ValueError
    #
    # If the maximum expression count is not limited and there are multiple thousand
    # values to join, PostgreSQL may reject the SQL statement with:
    # "django.db.utils.OperationalError: stack depth limit exceeded"
    max_expression_count: Optional[int] = None
    silent_drop_expression: bool = False

    def __init__(self, *expressions, output_field=None):
        super().__init__(output_field=output_field)
        if (
            self.max_expression_count is not None
            and len(expressions) > self.max_expression_count
        ):
            if self.silent_drop_expression:
                expressions = expressions[: self.max_expression_count]
                logger.warning(
                    "Maximum expression count exceed (%d out of %d)",
                    len(expressions),
                    self.max_expression_count,
                )
            else:
                raise ValueError("Maximum expression count exceeded")
        self.source_expressions: List[SearchVector] = self._parse_expressions(
            *expressions
        )

    def __repr__(self):
        args = self.arg_joiner.join(str(arg) for arg in self.source_expressions)
        return f"{self.__class__.__name__}({args})"

    def __add__(self, other):
        if not isinstance(other, FlatConcat):
            raise TypeError(
                f"Cannot combine FlatSearchVectorCombinable with other "
                f"instances types, got {other!r}."
            )
        return FlatConcat(*self.source_expressions + other.source_expressions)

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


class FlatConcatSearchVector(FlatConcat):
    max_expression_count = settings.INDEX_MAXIMUM_EXPR_COUNT
    silent_drop_expression = True
