"""Admin settings"""
from itertools import chain

from django.conf import settings
from django.contrib import admin

from social_core.utils import setting_name
from .models import UserSocialAuth, Nonce, Association


class UserSocialAuthOption(admin.ModelAdmin):
    """Social Auth user options"""
    list_display = ('user', 'id', 'provider', 'uid')
    list_filter = ('provider',)
    raw_id_fields = ('user',)
    list_select_related = True

    def get_search_fields(self, request=None):
        search_fields = getattr(
            settings, setting_name('ADMIN_USER_SEARCH_FIELDS'), None
        )
        if search_fields is None:
            _User = UserSocialAuth.user_model()
            username = getattr(_User, 'USERNAME_FIELD', None) or \
                       hasattr(_User, 'username') and 'username' or \
                       None
            fieldnames = ('first_name', 'last_name', 'email', username)
            all_names = self._get_all_field_names(_User._meta)
            search_fields = [name for name in fieldnames
                                if name and name in all_names]
        return ['user__' + name for name in search_fields] + \
            getattr(settings, setting_name('ADMIN_SEARCH_FIELDS'), [])

    @staticmethod
    def _get_all_field_names(model):
        names = chain.from_iterable(
            (field.name, field.attname)
                if hasattr(field, 'attname') else (field.name,)
            for field in model.get_fields()
            # For complete backwards compatibility, you may want to exclude
            # GenericForeignKey from the results.
            if not (field.many_to_one and field.related_model is None)
        )
        return list(set(names))


class NonceOption(admin.ModelAdmin):
    """Nonce options"""
    list_display = ('id', 'server_url', 'timestamp', 'salt')
    search_fields = ('server_url',)


class AssociationOption(admin.ModelAdmin):
    """Association options"""
    list_display = ('id', 'server_url', 'assoc_type')
    list_filter = ('assoc_type',)
    search_fields = ('server_url',)


admin.site.register(UserSocialAuth, UserSocialAuthOption)
admin.site.register(Nonce, NonceOption)
admin.site.register(Association, AssociationOption)
