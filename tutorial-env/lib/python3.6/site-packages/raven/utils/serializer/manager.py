"""
raven.utils.serializer.manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import logging
from contextlib import closing
from raven.utils.compat import text_type

__all__ = ('register', 'transform')

logger = logging.getLogger('sentry.errors.serializer')


class SerializationManager(object):
    logger = logger

    def __init__(self):
        self.__registry = []
        self.__serializers = {}

    @property
    def serializers(self):
        # XXX: Would serializers ever need state that we shouldn't cache them?
        for serializer in self.__registry:
            yield serializer

    def register(self, serializer):
        if serializer not in self.__registry:
            self.__registry.append(serializer)
        return serializer


class Serializer(object):
    logger = logger

    def __init__(self, manager):
        self.manager = manager
        self.context = set()
        self.serializers = []
        for serializer in manager.serializers:
            self.serializers.append(serializer(self))

    def close(self):
        del self.serializers
        del self.context

    def transform(self, value, **kwargs):
        """
        Primary function which handles recursively transforming
        values via their serializers
        """
        if value is None:
            return None

        objid = id(value)
        if objid in self.context:
            return '<...>'
        self.context.add(objid)

        try:
            for serializer in self.serializers:
                try:
                    if serializer.can(value):
                        return serializer.serialize(value, **kwargs)
                except Exception as e:
                    logger.exception(e)
                    return text_type(type(value))

            # if all else fails, lets use the repr of the object
            try:
                return repr(value)
            except Exception as e:
                logger.exception(e)
                # It's common case that a model's __unicode__ definition
                # may try to query the database which if it was not
                # cleaned up correctly, would hit a transaction aborted
                # exception
                return text_type(type(value))
        finally:
            self.context.remove(objid)


manager = SerializationManager()
register = manager.register


def transform(value, manager=manager, **kwargs):
    with closing(Serializer(manager)) as serializer:
        return serializer.transform(value, **kwargs)
