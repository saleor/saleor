from django.conf import settings
from django.contrib.auth import login, REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache

from social_core.utils import setting_name
from social_core.actions import do_auth, do_complete, do_disconnect
from .utils import psa


NAMESPACE = getattr(settings, setting_name('URL_NAMESPACE'), None) or 'social'

# Calling `session.set_expiry(None)` results in a session lifetime equal to
# platform default session lifetime.
DEFAULT_SESSION_TIMEOUT = None


@never_cache
@psa('{0}:complete'.format(NAMESPACE))
def auth(request, backend):
    return do_auth(request.backend, redirect_name=REDIRECT_FIELD_NAME)


@never_cache
@csrf_exempt
@psa('{0}:complete'.format(NAMESPACE))
def complete(request, backend, *args, **kwargs):
    """Authentication complete view"""
    return do_complete(request.backend, _do_login, user=request.user,
                       redirect_name=REDIRECT_FIELD_NAME, request=request,
                       *args, **kwargs)


@never_cache
@login_required
@psa()
@require_POST
@csrf_protect
def disconnect(request, backend, association_id=None):
    """Disconnects given backend from current logged in user."""
    return do_disconnect(request.backend, request.user, association_id,
                         redirect_name=REDIRECT_FIELD_NAME)


def get_session_timeout(social_user, enable_session_expiration=False,
                        max_session_length=None):
    if enable_session_expiration:
        # Retrieve an expiration date from the social user who just finished
        # logging in; this value was set by the social auth backend, and was
        # typically received from the server.
        expiration = social_user.expiration_datetime()

        # We've enabled session expiration. Check to see if we got
        # a specific expiration time from the provider for this user;
        # if not, use the platform default expiration.
        if expiration:
            received_expiration_time = expiration.total_seconds()
        else:
            received_expiration_time = DEFAULT_SESSION_TIMEOUT

        # Check to see if the backend set a value as a maximum length
        # that a session may be; if they did, then we should use the minimum
        # of that and the received session expiration time, if any, to
        # set the session length.
        if received_expiration_time is None and max_session_length is None:
            # We neither received an expiration length, nor have a maximum
            # session length. Use the platform default.
            session_expiry = DEFAULT_SESSION_TIMEOUT
        elif received_expiration_time is None and max_session_length is not None:
            # We only have a maximum session length; use that.
            session_expiry = max_session_length
        elif received_expiration_time is not None and max_session_length is None:
            # We only have an expiration time received by the backend
            # from the provider, with no set maximum. Use that.
            session_expiry = received_expiration_time
        else:
            # We received an expiration time from the backend, and we also
            # have a set maximum session length. Use the smaller of the two.
            session_expiry = min(received_expiration_time, max_session_length)
    else:
        # If there's an explicitly-set maximum session length, use that
        # even if we don't want to retrieve session expiry times from
        # the backend. If there isn't, then use the platform default.
        if max_session_length is None:
            session_expiry = DEFAULT_SESSION_TIMEOUT
        else:
            session_expiry = max_session_length

    return session_expiry


def _do_login(backend, user, social_user):
    user.backend = '{0}.{1}'.format(backend.__module__,
                                    backend.__class__.__name__)
    # Get these details early to avoid any issues involved in the
    # session switch that happens when we call login().
    enable_session_expiration = backend.setting('SESSION_EXPIRATION', False)
    max_session_length_setting = backend.setting('MAX_SESSION_LENGTH', None)

    # Log the user in, creating a new session.
    login(backend.strategy.request, user)

    # Make sure that the max_session_length value is either an integer or
    # None. Because we get this as a setting from the backend, it can be set
    # to whatever the backend creator wants; we want to be resilient against
    # unexpected types being presented to us.
    try:
        max_session_length = int(max_session_length_setting)
    except (TypeError, ValueError):
        # We got a response that doesn't look like a number; use the default.
        max_session_length = None

    # Get the session expiration length based on the maximum session length
    # setting, combined with any session length received from the backend.
    session_expiry = get_session_timeout(
        social_user,
        enable_session_expiration=enable_session_expiration,
        max_session_length=max_session_length,
    )

    try:
        # Set the session length to our previously determined expiry length.
        backend.strategy.request.session.set_expiry(session_expiry)
    except OverflowError:
        # The timestamp we used wasn't in the range of values supported by
        # Django for session length; use the platform default. We tried.
        backend.strategy.request.session.set_expiry(DEFAULT_SESSION_TIMEOUT)
