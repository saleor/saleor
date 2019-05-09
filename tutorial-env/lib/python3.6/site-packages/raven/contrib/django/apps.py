# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.apps import AppConfig


class RavenConfig(AppConfig):
    name = 'raven.contrib.django'
    label = 'raven_contrib_django'
    verbose_name = 'Raven'

    def ready(self):
        from .models import initialize
        initialize()
