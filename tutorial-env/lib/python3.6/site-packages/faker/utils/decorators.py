# coding=utf-8

from functools import wraps

from faker.utils import text


def slugify(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return text.slugify(fn(*args, **kwargs))
    return wrapper


def slugify_domain(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return text.slugify(fn(*args, **kwargs), allow_dots=True)
    return wrapper


def slugify_unicode(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return text.slugify(fn(*args, **kwargs), allow_unicode=True)
    return wrapper


def lowercase(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        return fn(*args, **kwargs).lower()
    return wrapper
