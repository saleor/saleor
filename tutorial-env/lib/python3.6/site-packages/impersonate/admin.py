#  -*- coding: utf-8 -*-
import logging
from django.contrib import admin
from django.utils.html import format_html
from django.db.utils import NotSupportedError

from .settings import settings
from .models import ImpersonationLog
from .helpers import User, check_allow_impersonate

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

logger = logging.getLogger(__name__)


def friendly_name(user):
    '''Return proper name if exists, else username.'''
    name = None
    if hasattr(user, 'get_full_name'):
        name = user.get_full_name()
    return name or getattr(user, getattr(User, 'USERNAME_FIELD', 'username'))


class SessionStateFilter(admin.SimpleListFilter):
    ''' Custom admin filter based on the session state.

        Provides two filter values - 'complete' and 'incomplete'.
        A session that has no session_ended_at timestamp is
        considered incomplete. This field is set from the
        session_end signal receiver.
    '''
    title = 'session state'
    parameter_name = 'session'

    def lookups(self, request, model_admin):
        return (
            ('incomplete', 'Incomplete'),
            ('complete', 'Complete'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'incomplete':
            return queryset.filter(session_ended_at__isnull=True)
        if self.value() == 'complete':
            return queryset.filter(session_ended_at__isnull=False)
        else:
            return queryset


class ImpersonatorFilter(admin.SimpleListFilter):
    ''' Custom admin filter based on the impersonator.

        Provides a set of users who have impersonated at some point.
        It is assumed that this is a small list of users - a subset
        of staff and superusers. There is no corresponding filter
        for users who have been impersonated, as this could be a
        very large set of users.

        If the number of unique impersonators exceeds MAX_FILTER_SIZE,
        then the filter is removed (shows only 'All').
    '''
    title = 'impersonator'
    parameter_name = 'impersonator'

    def lookups(self, request, model_admin):
        ''' Return list of unique users who have been an impersonator.
        '''
        # the queryset containing the ImpersonationLog objects
        MAX_FILTER_SIZE = settings.MAX_FILTER_SIZE
        try:
            # Evaluate here to raise exception if needed
            ids = list(
                model_admin.get_queryset(
                    request,
                ).order_by().values_list(
                    'impersonator_id',
                    flat=True,
                ).distinct('impersonator_id')
            )
        except (NotSupportedError, NotImplementedError):
            # Unit tests use sqlite db backend which doesn't support distinct.
            qs = model_admin.get_queryset(request).only('impersonator_id')
            ids = set([x.impersonator_id for x in qs])

        if len(ids) > MAX_FILTER_SIZE:
            logger.debug(
                ('Hiding admin list filter as number of impersonators [{0}] '
                 'exceeds MAX_FILTER_SIZE [{1}]').format(
                     len(ids),
                     MAX_FILTER_SIZE,
                 )
            )
            return

        impersonators = \
            User.objects.filter(id__in=ids).order_by(User.USERNAME_FIELD)
        for i in impersonators:
            yield (i.id, friendly_name(i))

    def queryset(self, request, queryset):
        if self.value() in (None, ''):
            return queryset
        else:
            return queryset.filter(impersonator_id=self.value())


class UserAdminImpersonateMixin(object):
    ''' Mixin to easily add user impersonation support via the Django
        admin change list page.
    '''
    open_new_window = False

    def get_list_display(self, request):
        if not check_allow_impersonate(request):
            return self.list_display
        list_display = list(self.list_display)
        list_display.append('impersonate_user')
        return list_display

    def impersonate_user(self, obj):
        target = ''
        if self.open_new_window:
            target = ' target="_blank"'
        return format_html(
            '<a href="{}"{}>Impersonate</a>',
            reverse('impersonate-start', args=[obj.id]),
            target,
        )
    impersonate_user.short_description = 'Impersonate User'


class ImpersonationLogAdmin(admin.ModelAdmin):
    list_display = (
        '_impersonator',
        '_impersonating',
        'session_key',
        'session_started_at',
        'duration'
    )
    readonly_fields = (
        'impersonator',
        'impersonating',
        'session_key',
        'session_started_at',
        'session_ended_at',
    )
    list_filter = (
        SessionStateFilter,
        ImpersonatorFilter,
        'session_started_at',
    )

    def _impersonator(self, obj):
        return friendly_name(obj.impersonator)

    def _impersonating(self, obj):
        return friendly_name(obj.impersonating)


admin.site.register(ImpersonationLog, ImpersonationLogAdmin)
