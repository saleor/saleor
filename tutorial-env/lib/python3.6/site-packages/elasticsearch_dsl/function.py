import collections

from .utils import DslBase

def SF(name_or_sf, **params):
    # {"script_score": {"script": "_score"}, "filter": {}}
    if isinstance(name_or_sf, collections.Mapping):
        if params:
            raise ValueError('SF() cannot accept parameters when passing in a dict.')
        kwargs = {}
        sf = name_or_sf.copy()
        for k in ScoreFunction._param_defs:
            if k in name_or_sf:
                kwargs[k] = sf.pop(k)

        # not sf, so just filter+weight, which used to be boost factor
        if not sf:
            name = 'boost_factor'
        # {'FUNCTION': {...}}
        elif len(sf) == 1:
            name, params = sf.popitem()
        else:
            raise ValueError('SF() got an unexpected fields in the dictionary: %r' % sf)

        # boost factor special case, see elasticsearch #6343
        if not isinstance(params, collections.Mapping):
            params = {'value': params}

        # mix known params (from _param_defs) and from inside the function
        kwargs.update(params)
        return ScoreFunction.get_dsl_class(name)(**kwargs)

    # ScriptScore(script="_score", filter=Q())
    if isinstance(name_or_sf, ScoreFunction):
        if params:
            raise ValueError('SF() cannot accept parameters when passing in a ScoreFunction object.')
        return name_or_sf

    # "script_score", script="_score", filter=Q()
    return ScoreFunction.get_dsl_class(name_or_sf)(**params)

class ScoreFunction(DslBase):
    _type_name = 'score_function'
    _type_shortcut = staticmethod(SF)
    _param_defs = {
        'query': {'type': 'query'},
        'filter': {'type': 'query'},
        'weight': {}
    }
    name = None

    def to_dict(self):
        d = super(ScoreFunction, self).to_dict()
        # filter and query dicts should be at the same level as us
        for k in self._param_defs:
            if k in d[self.name]:
                d[k] = d[self.name].pop(k)
        return d

class ScriptScore(ScoreFunction):
    name = 'script_score'

class BoostFactor(ScoreFunction):
    name = 'boost_factor'

    def to_dict(self):
        d = super(BoostFactor, self).to_dict()
        if 'value' in d[self.name]:
            d[self.name] = d[self.name].pop('value')
        else:
            del d[self.name]
        return d

class RandomScore(ScoreFunction):
    name = 'random_score'

class FieldValueFactor(ScoreFunction):
    name = 'field_value_factor'

class Linear(ScoreFunction):
    name = 'linear'

class Gauss(ScoreFunction):
    name = 'gauss'

class Exp(ScoreFunction):
    name = 'exp'

