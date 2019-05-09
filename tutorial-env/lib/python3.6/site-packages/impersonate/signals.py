# -*- coding: utf-8 -*-
import logging
import hashlib
from django.dispatch import Signal, receiver
from django.utils.timezone import now as tz_now
from django.utils.crypto import get_random_string

from .settings import settings
from .models import ImpersonationLog

logger = logging.getLogger(__name__)

# signal sent when an impersonation session begins
session_begin = Signal(
    providing_args=['impersonator', 'impersonating', 'request']
)

# signal sent when an impersonation session ends
session_end = Signal(
    providing_args=['impersonator', 'impersonating', 'request']
)


def gen_unique_id():
    return hashlib.sha1(
        u'{0}:{1}'.format(get_random_string(), tz_now()).encode('utf-8')
    ).hexdigest()


@receiver(session_begin, dispatch_uid='impersonate.signals.on_session_begin')
def on_session_begin(sender, **kwargs):
    ''' Create a new ImpersonationLog object.
    '''
    impersonator = kwargs.get('impersonator')
    impersonating = kwargs.get('impersonating')
    logger.info(u'{0} has started impersonating {1}.'.format(
        impersonator,
        impersonating,
    ))

    if settings.DISABLE_LOGGING:
        return

    request = kwargs.get('request')
    session_key = gen_unique_id()

    ImpersonationLog.objects.create(
        impersonator=impersonator,
        impersonating=impersonating,
        session_key=session_key,
        session_started_at=tz_now()
    )

    request.session['_impersonate_session_id'] = session_key
    request.session.modified = True



@receiver(session_end, dispatch_uid='impersonate.signals.on_session_end')
def on_session_end(sender, **kwargs):
    ''' Update ImpersonationLog with the end timestamp.

        This uses the combination of session_key, impersonator and
        user being impersonated to look up the corresponding
        impersonation log object.
    '''
    impersonator = kwargs.get('impersonator')
    impersonating = kwargs.get('impersonating')
    logger.info(u'{0} has finished impersonating {1}.'.format(
        impersonator,
        impersonating,
    ))

    if settings.DISABLE_LOGGING:
        return

    request = kwargs.get('request')
    session_key = request.session.get('_impersonate_session_id', None)

    try:
        # look for unfinished sessions that match impersonator / subject
        log = ImpersonationLog.objects.get(
                impersonator=impersonator,
                impersonating=impersonating,
                session_key=session_key,
                session_ended_at__isnull=True,
        )
        log.session_ended_at = tz_now()
        log.save()
    except ImpersonationLog.DoesNotExist:
        logger.warning(
            (u'Unfinished ImpersonationLog could not be found for: '
             u'{0}, {1}, {2}').format(
                 impersonator,
                 impersonating,
                 session_key,
             )
        )
    except ImpersonationLog.MultipleObjectsReturned:
        logger.warning(
            (u'Multiple unfinished ImpersonationLog matching: '
             u'{0}, {1}, {2}').format(
                 impersonator,
                 impersonating,
                 session_key,
             )
        )

    del request.session['_impersonate_session_id']
    request.session.modified = True
