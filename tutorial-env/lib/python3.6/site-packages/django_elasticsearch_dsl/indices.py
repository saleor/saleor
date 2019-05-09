from copy import deepcopy

from django.utils.encoding import python_2_unicode_compatible
from elasticsearch_dsl import Index as DSLIndex

from .apps import DEDConfig
from .registries import registry


@python_2_unicode_compatible
class Index(DSLIndex):
    def __init__(self, name, using='default'):
        super(Index, self).__init__(name, using)
        self._settings = deepcopy(DEDConfig.default_index_settings())

    def doc_type(self, doc_type, *args, **kwargs):
        """
        Extend to register the doc_type in the global document registry
        """
        doc_type = super(Index, self).doc_type(doc_type, *args, **kwargs)
        registry.register(self, doc_type)
        return doc_type

    def __str__(self):
        return self._name
