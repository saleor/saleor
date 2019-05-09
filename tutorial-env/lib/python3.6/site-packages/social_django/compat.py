# coding=utf-8
import six
import django
from django.db import models


try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object


def get_rel_model(field):
    if django.VERSION >= (1, 9):
        return field.remote_field.model

    user_model = field.rel.to
    if isinstance(user_model, six.string_types):
        app_label, model_name = user_model.split('.')
        user_model = models.get_model(app_label, model_name)
    return user_model


def get_request_port(request):
    if django.VERSION >= (1, 9):
        return request.get_port()

    host_parts = request.get_host().partition(':')
    return host_parts[2] or request.META['SERVER_PORT']
