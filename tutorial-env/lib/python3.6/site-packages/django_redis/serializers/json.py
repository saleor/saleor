# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import json

from django.core.serializers.json import DjangoJSONEncoder

from .base import BaseSerializer


class JSONSerializer(BaseSerializer):
    def dumps(self, value):
        return json.dumps(value, cls=DjangoJSONEncoder).encode()

    def loads(self, value):
        return json.loads(value.decode())
