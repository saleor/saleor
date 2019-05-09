from .utils import DslBase

__all__ = [
    'tokenizer', 'analyzer', 'char_filter', 'token_filter', 'normalizer'
]

class AnalysisBase(object):
    @classmethod
    def _type_shortcut(cls, name_or_instance, type=None, **kwargs):
        if isinstance(name_or_instance, cls):
            if type or kwargs:
                raise ValueError('%s() cannot accept parameters.' % cls.__name__)
            return name_or_instance

        if not (type or kwargs):
            return cls.get_dsl_class('builtin')(name_or_instance)

        return cls.get_dsl_class('custom')(name_or_instance, type or 'custom', **kwargs)

class CustomAnalysis(object):
    name = 'custom'
    def __init__(self, filter_name, builtin_type='custom', **kwargs):
        self._builtin_type = builtin_type
        self._name = filter_name
        super(CustomAnalysis, self).__init__(**kwargs)

    def to_dict(self):
        # only name to present in lists
        return self._name

    def get_definition(self):
        d = super(CustomAnalysis, self).to_dict()
        d = d.pop(self.name)
        d['type'] = self._builtin_type
        return d

class CustomAnalysisDefinition(CustomAnalysis):
    def get_analysis_definition(self):
        out = {self._type_name: {self._name: self.get_definition()}}

        t = getattr(self, 'tokenizer', None)
        if 'tokenizer' in self._param_defs and hasattr(t, 'get_definition'):
            out['tokenizer'] = {t._name: t.get_definition()}

        filters = dict((f._name, f.get_definition())
                       for f in self.filter if hasattr(f, 'get_definition'))
        if filters:
            out['filter'] = filters

        char_filters = dict((f._name, f.get_definition())
                            for f in self.char_filter if hasattr(f, 'get_definition'))
        if char_filters:
            out['char_filter'] = char_filters

        return out

class BuiltinAnalysis(object):
    name = 'builtin'
    def __init__(self, name):
        self._name = name
        super(BuiltinAnalysis, self).__init__()

    def to_dict(self):
        # only name to present in lists
        return self._name

class Analyzer(AnalysisBase, DslBase):
    _type_name = 'analyzer'
    name = None

class BuiltinAnalyzer(BuiltinAnalysis, Analyzer):
    def get_analysis_definition(self):
        return {}

class CustomAnalyzer(CustomAnalysisDefinition, Analyzer):
    _param_defs = {
        'filter': {'type': 'token_filter', 'multi': True},
        'char_filter': {'type': 'char_filter', 'multi': True},
        'tokenizer': {'type': 'tokenizer'},
    }

class Normalizer(AnalysisBase, DslBase):
    _type_name = 'normalizer'
    name = None

class BuiltinNormalizer(BuiltinAnalysis, Normalizer):
    def get_analysis_definition(self):
        return {}

class CustomNormalizer(CustomAnalysisDefinition, Normalizer):
    _param_defs = {
        'filter': {'type': 'token_filter', 'multi': True},
        'char_filter': {'type': 'char_filter', 'multi': True}
    }

class Tokenizer(AnalysisBase, DslBase):
    _type_name = 'tokenizer'
    name = None

class BuiltinTokenizer(BuiltinAnalysis, Tokenizer):
    pass

class CustomTokenizer(CustomAnalysis, Tokenizer):
    pass


class TokenFilter(AnalysisBase, DslBase):
    _type_name = 'token_filter'
    name = None

class BuiltinTokenFilter(BuiltinAnalysis, TokenFilter):
    pass

class CustomTokenFilter(CustomAnalysis, TokenFilter):
    pass


class CharFilter(AnalysisBase, DslBase):
    _type_name = 'char_filter'
    name = None

class BuiltinCharFilter(BuiltinAnalysis, CharFilter):
    pass

class CustomCharFilter(CustomAnalysis, CharFilter):
    pass


# shortcuts for direct use
analyzer = Analyzer._type_shortcut
tokenizer = Tokenizer._type_shortcut
token_filter = TokenFilter._type_shortcut
char_filter = CharFilter._type_shortcut
normalizer = Normalizer._type_shortcut
