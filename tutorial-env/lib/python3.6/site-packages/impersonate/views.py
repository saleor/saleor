# -*- coding: utf-8 -*-
import logging
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .settings import User, settings
from .decorators import allowed_user_required
from .signals import session_begin, session_end
from .helpers import (
    get_redir_path, get_redir_arg, get_paginator, get_redir_field,
    check_allow_for_user, users_impersonable
)

logger = logging.getLogger(__name__)


@allowed_user_required
def impersonate(request, uid):
    ''' Takes in the UID of the user to impersonate.
        View will fetch the User instance and store it
        in the request.session under the '_impersonate' key.

        The middleware will then pick up on it and adjust the
        request object as needed.

        Also store the user's 'starting'/'original' URL so
        we can return them to it.
    '''
    new_user = get_object_or_404(User, pk=uid)
    if check_allow_for_user(request, new_user):
        request.session['_impersonate'] = new_user.pk
        prev_path = request.META.get('HTTP_REFERER')
        if prev_path:
            request.session['_impersonate_prev_path'] = \
                                request.build_absolute_uri(prev_path)

        request.session.modified = True  # Let's make sure...
        # can be used to hook up auditing of the session
        session_begin.send(
            sender=None,
            impersonator=request.user,
            impersonating=new_user,
            request=request
        )
    return redirect(get_redir_path(request))


def stop_impersonate(request):
    ''' Remove the impersonation object from the session
        and ideally return the user to the original path
        they were on.
    '''
    impersonating = request.session.pop('_impersonate', None)
    if impersonating is not None:
        try:
            impersonating = User.objects.get(pk=impersonating)
        except User.DoesNotExist:
            # Should never be reached.
            logger.info(
                (u'NOTICE: User being impersonated (PK '
                 u'{0}) no longer exists.').format(impersonating)
            )
            impersonating = None

    original_path = request.session.pop('_impersonate_prev_path', None)
    use_refer = settings.USE_HTTP_REFERER

    if impersonating is not None:
        request.session.modified = True
        session_end.send(
            sender=None,
            impersonator=request.impersonator,
            impersonating=impersonating,
            request=request
        )

    dest = original_path \
        if original_path and use_refer else get_redir_path(request)
    return redirect(dest)


@allowed_user_required
def list_users(request, template):
    ''' List all users in the system.
        Will add 5 items to the context.
          * users - queryset of all users
          * paginator - Django Paginator instance
          * page - Current page of objects (from Paginator)
          * page_number - Current page number, defaults to 1
          * redirect - arg for redirect target, e.g. "?next=/foo/bar"
    '''
    users = users_impersonable(request)

    paginator, page, page_number = get_paginator(request, users)

    return render(request, template, {
        'users': users,
        'paginator': paginator,
        'page': page,
        'page_number': page_number,
        'redirect': get_redir_arg(request),
        'redirect_field': get_redir_field(request),
    })


@allowed_user_required
def search_users(request, template):
    ''' Simple search through the users.
        Will add 7 items to the context.
          * users - All users that match the query passed.
          * paginator - Django Paginator instance
          * page - Current page of objects (from Paginator)
          * page_number - Current page number, defaults to 1
          * query - The search query that was entered
          * redirect - arg for redirect target, e.g. "?next=/foo/bar"
          * redirect_field - hidden input field with redirect argument,
                              put this inside search form
    '''
    query = request.GET.get('q', u'')

    # define search fields and lookup type
    search_fields = set(settings.SEARCH_FIELDS)
    lookup_type = settings.LOOKUP_TYPE

    # prepare kwargs
    search_q = Q()
    for term in query.split():
        sub_q = Q()
        for search_field in search_fields:
            sub_q |= Q(**{'{0}__{1}'.format(search_field, lookup_type): term})
        search_q &= sub_q

    users = users_impersonable(request)
    users = users.filter(search_q).distinct()
    paginator, page, page_number = get_paginator(request, users)

    return render(request, template, {
        'users': users,
        'paginator': paginator,
        'page': page,
        'page_number': page_number,
        'query': query,
        'redirect': get_redir_arg(request),
        'redirect_field': get_redir_field(request),
    })
