from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class RefreshTokenConfig(AppConfig):
    name = 'graphql_jwt.refresh_token'
    verbose_name = _('Refresh token')
