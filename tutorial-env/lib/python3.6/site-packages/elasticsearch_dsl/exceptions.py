class ElasticsearchDslException(Exception):
    pass


class UnknownDslObject(ElasticsearchDslException):
    pass


class ValidationException(ValueError, ElasticsearchDslException):
    pass


class IllegalOperation(ElasticsearchDslException):
    pass
