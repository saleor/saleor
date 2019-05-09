class DjangoElasticsearchDslError(Exception):
    pass


class VariableLookupError(DjangoElasticsearchDslError):
    pass


class RedeclaredFieldError(DjangoElasticsearchDslError):
    pass


class ModelFieldNotMappedError(DjangoElasticsearchDslError):
    pass
