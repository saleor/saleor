from django.contrib.postgres.search import (
    CombinedSearchVector,
    SearchVector,
    SearchVectorCombinable,
)


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
