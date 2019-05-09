import collections

from .utils import DslBase
from .response.aggs import BucketData, FieldBucketData, AggResponse, TopHitsData

def A(name_or_agg, filter=None, **params):
    if filter is not None:
        if name_or_agg != 'filter':
            raise ValueError("Aggregation %r doesn't accept positional argument 'filter'." % name_or_agg)
        params['filter'] = filter

    # {"terms": {"field": "tags"}, "aggs": {...}}
    if isinstance(name_or_agg, collections.Mapping):
        if params:
            raise ValueError('A() cannot accept parameters when passing in a dict.')
        # copy to avoid modifying in-place
        agg = name_or_agg.copy()
        # pop out nested aggs
        aggs = agg.pop('aggs', None)
        # pop out meta data
        meta = agg.pop('meta', None)
        # should be {"terms": {"field": "tags"}}
        if len(agg) != 1:
            raise ValueError('A() can only accept dict with an aggregation ({"terms": {...}}). '
                             'Instead it got (%r)' % name_or_agg)
        agg_type, params = agg.popitem()
        if aggs:
            params = params.copy()
            params['aggs'] = aggs
        if meta:
            params = params.copy()
            params['meta'] = meta
        return Agg.get_dsl_class(agg_type)(_expand__to_dot=False, **params)

    # Terms(...) just return the nested agg
    elif isinstance(name_or_agg, Agg):
        if params:
            raise ValueError('A() cannot accept parameters when passing in an Agg object.')
        return name_or_agg

    # "terms", field="tags"
    return Agg.get_dsl_class(name_or_agg)(**params)

class Agg(DslBase):
    _type_name = 'agg'
    _type_shortcut = staticmethod(A)
    name = None

    def __contains__(self, key):
        return False

    def to_dict(self):
        d = super(Agg, self).to_dict()
        if 'meta' in d[self.name]:
            d['meta'] = d[self.name].pop('meta')
        return d

    def result(self, search, data):
        return AggResponse(self, search, data)


class AggBase(object):
    _param_defs = {
        'aggs': {'type': 'agg', 'hash': True},
    }
    def __contains__(self, key):
        return key in self._params.get('aggs', {})

    def __getitem__(self, agg_name):
        agg = self._params.setdefault('aggs', {})[agg_name]  # propagate KeyError

        # make sure we're not mutating a shared state - whenever accessing a
        # bucket, return a shallow copy of it to be safe
        if isinstance(agg, Bucket):
            agg = A(agg.name, **agg._params)
            # be sure to store the copy so any modifications to it will affect us
            self._params['aggs'][agg_name] = agg

        return agg

    def __setitem__(self, agg_name, agg):
        self.aggs[agg_name] = A(agg)

    def __iter__(self):
        return iter(self.aggs)

    def _agg(self, bucket, name, agg_type, *args, **params):
        agg = self[name] = A(agg_type, *args, **params)

        # For chaining - when creating new buckets return them...
        if bucket:
            return agg
        # otherwise return self._base so we can keep chaining
        else:
            return self._base

    def metric(self, name, agg_type, *args, **params):
        return self._agg(False, name, agg_type, *args, **params)

    def bucket(self, name, agg_type, *args, **params):
        return self._agg(True, name, agg_type, *args, **params)

    def pipeline(self, name, agg_type, *args, **params):
        return self._agg(False, name, agg_type, *args, **params)

    def result(self, search, data):
        return BucketData(self, search, data)


class Bucket(AggBase, Agg):
    def __init__(self, **params):
        super(Bucket, self).__init__(**params)
        # remember self for chaining
        self._base = self

    def to_dict(self):
        d = super(AggBase, self).to_dict()
        if 'aggs' in d[self.name]:
            d['aggs'] = d[self.name].pop('aggs')
        return d

class Filter(Bucket):
    name = 'filter'
    _param_defs = {
        'filter': {'type': 'query'},
        'aggs': {'type': 'agg', 'hash': True},
    }

    def __init__(self, filter=None, **params):
        if filter is not None:
            params['filter'] = filter
        super(Filter, self).__init__(**params)

    def to_dict(self):
        d = super(Filter, self).to_dict()
        d[self.name].update(d[self.name].pop('filter', {}))
        return d

class Pipeline(Agg):
    pass

# bucket aggregations
class Filters(Bucket):
    name = 'filters'
    _param_defs = {
        'filters': {'type': 'query', 'hash': True},
        'aggs': {'type': 'agg', 'hash': True},
    }

class Children(Bucket):
    name = 'children'

class DateHistogram(Bucket):
    name = 'date_histogram'

    def result(self, search, data):
        return FieldBucketData(self, search, data)

class DateRange(Bucket):
    name = 'date_range'

class GeoDistance(Bucket):
    name = 'geo_distance'

class GeohashGrid(Bucket):
    name = 'geohash_grid'

class GeoCentroid(Bucket):
    name = 'geo_centroid'

class Global(Bucket):
    name = 'global'

class Histogram(Bucket):
    name = 'histogram'
    def result(self, search, data):
        return FieldBucketData(self, search, data)

# TODO: remove in 6.0
class Iprange(Bucket):
    name = 'ip_range'

class IPRange(Bucket):
    name = 'ip_range'

class Missing(Bucket):
    name = 'missing'

class Nested(Bucket):
    name = 'nested'

class Range(Bucket):
    name = 'range'

class ReverseNested(Bucket):
    name = 'reverse_nested'

class SignificantTerms(Bucket):
    name = 'significant_terms'

class Terms(Bucket):
    name = 'terms'

    def result(self, search, data):
        return FieldBucketData(self, search, data)

class Sampler(Bucket):
    name = 'sampler'

class DiversifiedSampler(Bucket):
    name = 'diversified_sampler'

# metric aggregations
class TopHits(Agg):
    name = 'top_hits'

    def result(self, search, data):
        return TopHitsData(self, search, data)

class Avg(Agg):
    name = 'avg'

class Cardinality(Agg):
    name = 'cardinality'

class ExtendedStats(Agg):
    name = 'extended_stats'

class GeoBounds(Agg):
    name = 'geo_bounds'

class Max(Agg):
    name = 'max'

class Min(Agg):
    name = 'min'

class Percentiles(Agg):
    name = 'percentiles'

class PercentileRanks(Agg):
    name = 'percentile_ranks'

class ScriptedMetric(Agg):
    name = 'scripted_metric'

class Stats(Agg):
    name = 'stats'

class Sum(Agg):
    name = 'sum'

class ValueCount(Agg):
    name = 'value_count'

# pipeline aggregations
class AvgBucket(Pipeline):
    name = 'avg_bucket'

class BucketScript(Pipeline):
    name = 'bucket_script'

class BucketSelector(Pipeline):
    name = 'bucket_selector'

class CumulativeSum(Pipeline):
    name = 'cumulative_sum'

class Derivative(Pipeline):
    name = 'derivative'

class ExtendedStatsBucket(Pipeline):
    name = 'extended_stats_bucket'

class MaxBucket(Pipeline):
    name = 'max_bucket'

class MinBucket(Pipeline):
    name = 'min_bucket'

class MovingAvg(Pipeline):
    name = 'moving_avg'

class PercentilesBucket(Pipeline):
    name = 'percentiles_bucket'

class SerialDiff(Pipeline):
    name = 'serial_diff'

class StatsBucket(Pipeline):
    name = 'stats_bucket'

class SumBucket(Pipeline):
    name = 'sum_bucket'
