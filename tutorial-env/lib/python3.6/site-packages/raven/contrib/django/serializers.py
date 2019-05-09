"""
raven.contrib.django.serializers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import
from __future__ import unicode_literals

from django.conf import settings
from django.http import HttpRequest
from django.utils.functional import Promise
from raven.utils.serializer import Serializer, register
from raven.utils.compat import text_type

__all__ = ('PromiseSerializer',)


class PromiseSerializer(Serializer):
    types = (Promise,)

    def can(self, value):
        if not super(PromiseSerializer, self).can(value):
            return False

        pre = value.__class__.__name__[1:]
        if not (hasattr(value, '%s__func' % pre) or
                hasattr(value, '%s__unicode_cast' % pre) or
                hasattr(value, '%s__text_cast' % pre)):
            return False

        return True

    def serialize(self, value, **kwargs):
        # EPIC HACK
        # handles lazy model instances (which are proxy values that don't
        # easily give you the actual function)
        pre = value.__class__.__name__[1:]
        if hasattr(value, '%s__func' % pre):
            value = getattr(value, '%s__func' % pre)(
                *getattr(value, '%s__args' % pre),
                **getattr(value, '%s__kw' % pre))
        else:
            return self.recurse(text_type(value))
        return self.recurse(value, **kwargs)


register(PromiseSerializer)


class HttpRequestSerializer(Serializer):
    types = (HttpRequest,)

    def serialize(self, value, **kwargs):
        return '<%s at 0x%s>' % (type(value).__name__, id(value))


register(HttpRequestSerializer)


if getattr(settings, 'DATABASES', None):
    from django.db.models.query import QuerySet

    class QuerySetSerializer(Serializer):
        types = (QuerySet,)

        def serialize(self, value, **kwargs):
            qs_name = type(value).__name__
            if value.model:
                return '<%s: model=%s>' % (qs_name, value.model.__name__)
            return '<%s: (Unbound)>' % (qs_name,)

    register(QuerySetSerializer)
