# -*- coding: utf-8 -*-
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'impersonate'

    def ready(self):
        from . import signals
