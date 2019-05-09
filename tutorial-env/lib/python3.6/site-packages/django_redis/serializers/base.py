# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals


class BaseSerializer(object):
    def __init__(self, options):
        pass

    def dumps(self, value):
        raise NotImplementedError

    def loads(self, value):
        raise NotImplementedError
