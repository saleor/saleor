import collections

from itertools import chain

from .utils import DslBase
from .function import SF, ScoreFunction


def Q(name_or_query='match_all', **params):
    # {"match": {"title": "python"}}
    if isinstance(name_or_query, collections.Mapping):
        if params:
            raise ValueError('Q() cannot accept parameters when passing in a dict.')
        if len(name_or_query) != 1:
            raise ValueError('Q() can only accept dict with a single query ({"match": {...}}). '
                 'Instead it got (%r)' % name_or_query)
        name, params = name_or_query.copy().popitem()
        return Query.get_dsl_class(name)(_expand__to_dot=False, **params)

    # MatchAll()
    if isinstance(name_or_query, Query):
        if params:
            raise ValueError('Q() cannot accept parameters when passing in a Query object.')
        return name_or_query

    # s.query = Q('filtered', query=s.query)
    if hasattr(name_or_query, '_proxied'):
        return name_or_query._proxied

    # "match", title="python"
    return Query.get_dsl_class(name_or_query)(**params)

class Query(DslBase):
    _type_name = 'query'
    _type_shortcut = staticmethod(Q)
    name = None

    def __add__(self, other):
        # make sure we give queries that know how to combine themselves
        # preference
        if hasattr(other, '__radd__'):
            return other.__radd__(self)
        return Bool(must=[self, other])

    def __invert__(self):
        return Bool(must_not=[self])

    def __or__(self, other):
        # make sure we give queries that know how to combine themselves
        # preference
        if hasattr(other, '__ror__'):
            return other.__ror__(self)
        return Bool(should=[self, other])

    def __and__(self, other):
        # make sure we give queries that know how to combine themselves
        # preference
        if hasattr(other, '__rand__'):
            return other.__rand__(self)
        return Bool(must=[self, other])


class MatchAll(Query):
    name = 'match_all'
    def __add__(self, other):
        return other._clone()
    __and__ = __rand__ = __radd__ = __add__

    def __or__(self, other):
        return self
    __ror__ = __or__
EMPTY_QUERY = MatchAll()

class Bool(Query):
    name = 'bool'
    _param_defs = {
        'must': {'type': 'query', 'multi': True},
        'should': {'type': 'query', 'multi': True},
        'must_not': {'type': 'query', 'multi': True},
        'filter': {'type': 'query', 'multi': True},
    }

    def __add__(self, other):
        q = self._clone()
        if isinstance(other, Bool):
            q.must += other.must
            q.should += other.should
            q.must_not += other.must_not
            q.filter += other.filter
        else:
            q.must.append(other)
        return q
    __radd__ = __add__

    def __or__(self, other):
        for q in (self, other):
            if isinstance(q, Bool) and not any((q.must, q.must_not, q.filter)):
                # TODO: take minimum_should_match into account
                other = self if q is other else other
                q = q._clone()
                if isinstance(other, Bool) and not any((other.must, other.must_not, other.filter)):
                    q.should.extend(other.should)
                else:
                    q.should.append(other)
                return q

        return Bool(should=[self, other])
    __ror__ = __or__

    @property
    def _min_should_match(self):
        return getattr(self, 'minimum_should_match', 0 if not self.should or (self.must or self.filter) else 1)

    def __invert__(self):
        negations = []
        for q in chain(self.must, self.filter):
            negations.append(~q)

        for q in self.must_not:
            negations.append(q)

        if self.should and self._min_should_match:
            negations.append(Bool(must_not=self.should[:]))

        if len(negations) == 1:
            return negations[0]
        return Bool(should=negations)

    def __and__(self, other):
        q = self._clone()
        if isinstance(other, Bool):
            q.must += other.must
            q.must_not += other.must_not
            q.filter += other.filter
            q.should = []
            for qx in (self, other):
                # TODO: percentages will fail here
                min_should_match = qx._min_should_match
                # all subqueries are required
                if len(qx.should) <= min_should_match:
                    q.must.extend(qx.should)
                # not all of them are required, use it and remember min_should_match
                elif not q.should:
                    q.minimum_should_match = min_should_match
                    q.should = qx.should
                # all queries are optional, just extend should
                elif q._min_should_match == 0 and min_should_match == 0:
                    q.should.extend(qx.should)
                # not all are required, add a should list to the must with proper min_should_match
                else:
                    q.must.append(Bool(should=qx.should, minimum_should_match=min_should_match))
        else:
            if not (q.must or q.filter) and q.should:
                q._params.setdefault('minimum_should_match', 1)
            q.must.append(other)
        return q
    __rand__ = __and__

class FunctionScore(Query):
    name = 'function_score'
    _param_defs = {
        'query': {'type': 'query'},
        'filter': {'type': 'query'},
        'functions': {'type': 'score_function', 'multi': True},
    }

    def __init__(self, **kwargs):
        if 'functions' in kwargs:
            pass
        else:
            fns = kwargs['functions'] = []
            for name in ScoreFunction._classes:
                if name in kwargs:
                    fns.append({name: kwargs.pop(name)})
        super(FunctionScore, self).__init__(**kwargs)


# compound queries
class Boosting(Query):
    name = 'boosting'
    _param_defs = {'positive': {'type': 'query'}, 'negative': {'type': 'query'}}

class ConstantScore(Query):
    name = 'constant_score'
    _param_defs = {'query': {'type': 'query'}, 'filter': {'type': 'query'}}

class DisMax(Query):
    name = 'dis_max'
    _param_defs = {'queries': {'type': 'query', 'multi': True}}

class Filtered(Query):
    name = 'filtered'
    _param_defs = {'query': {'type': 'query'}, 'filter': {'type': 'query'}}

class Indices(Query):
    name = 'indices'
    _param_defs = {'query': {'type': 'query'}, 'no_match_query': {'type': 'query'}}


# relationship queries
class Nested(Query):
    name = 'nested'
    _param_defs = {'query': {'type': 'query'}}

class HasChild(Query):
    name = 'has_child'
    _param_defs = {'query': {'type': 'query'}}

class HasParent(Query):
    name = 'has_parent'
    _param_defs = {'query': {'type': 'query'}}

class TopChildren(Query):
    name = 'top_children'
    _param_defs = {'query': {'type': 'query'}}


# compount span queries
class SpanFirst(Query):
    name = 'span_first'
    _param_defs = {'match': {'type': 'query'}}

class SpanMulti(Query):
    name = 'span_multi'
    _param_defs = {'match': {'type': 'query'}}

class SpanNear(Query):
    name = 'span_near'
    _param_defs = {'clauses': {'type': 'query', 'multi': True}}

class SpanNot(Query):
    name = 'span_not'
    _param_defs = {'exclude': {'type': 'query'}, 'include': {'type': 'query'}}

class SpanOr(Query):
    name = 'span_or'
    _param_defs = {'clauses': {'type': 'query', 'multi': True}}

class FieldMaskingSpan(Query):
    name = 'field_masking_span'
    _param_defs = {'query': {'type': 'query'}}

class SpanContainining(Query):
    name = 'span_containing'
    _param_defs = {'little': {'type': 'query'}, 'big': {'type': 'query'}}

class SpanWithin(Query):
    name = 'span_within'
    _param_defs = {'little': {'type': 'query'}, 'big': {'type': 'query'}}

# core queries
class Common(Query):
    name = 'common'

class Fuzzy(Query):
    name = 'fuzzy'

class FuzzyLikeThis(Query):
    name = 'fuzzy_like_this'

class FuzzyLikeThisField(Query):
    name = 'fuzzy_like_this_field'

class GeoBoundingBox(Query):
    name = 'geo_bounding_box'

class GeoDistance(Query):
    name = 'geo_distance'

class GeoDistanceRange(Query):
    name = 'geo_distance_range'

class GeoPolygon(Query):
    name = 'geo_polygon'

class GeoShape(Query):
    name = 'geo_shape'

class GeohashCell(Query):
    name = 'geohash_cell'

class Ids(Query):
    name = 'ids'

class Limit(Query):
    name = 'limit'

class Match(Query):
    name = 'match'

class MatchPhrase(Query):
    name = 'match_phrase'

class MatchPhrasePrefix(Query):
    name = 'match_phrase_prefix'

class Exists(Query):
    name = 'exists'

class MoreLikeThis(Query):
    name = 'more_like_this'

class MoreLikeThisField(Query):
    name = 'more_like_this_field'

class MultiMatch(Query):
    name = 'multi_match'

class Prefix(Query):
    name = 'prefix'

class QueryString(Query):
    name = 'query_string'

class Range(Query):
    name = 'range'

class Regexp(Query):
    name = 'regexp'

class SimpleQueryString(Query):
    name = 'simple_query_string'

class SpanTerm(Query):
    name = 'span_term'

class Template(Query):
    name = 'template'

class Term(Query):
    name = 'term'

class Terms(Query):
    name = 'terms'

class Wildcard(Query):
    name = 'wildcard'

class Script(Query):
    name = 'script'

class Type(Query):
    name = 'type'

class ParentId(Query):
    name = 'parent_id'
