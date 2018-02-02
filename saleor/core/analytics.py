import uuid

from celery import shared_task
from django.conf import settings
import google_measurement_protocol as ga

FINGERPRINT_PARTS = [
    'HTTP_ACCEPT_ENCODING',
    'HTTP_ACCEPT_LANGUAGE',
    'HTTP_USER_AGENT',
    'HTTP_X_FORWARDED_FOR',
    'REMOTE_ADDR']

UUID_NAMESPACE = uuid.UUID('fb4abc05-e2fb-4e3e-8b78-28037ef7d07f')


def get_client_id(request):
    parts = [request.META.get(key, '') for key in FINGERPRINT_PARTS]
    name = '_'.join(parts)
    return uuid.uuid5(UUID_NAMESPACE, name)


@shared_task
def ga_report(tracking_id, client_id, what, extra_info=None,
              extra_headers=None):
    ga.report(tracking_id, client_id, what, extra_info=extra_info,
              extra_headers=extra_headers)


def _report(client_id, what, extra_info=None, extra_headers=None):
    tracking_id = getattr(settings, 'GOOGLE_ANALYTICS_TRACKING_ID', None)
    if tracking_id and client_id:
        ga_report(tracking_id, client_id, what, extra_info=extra_info,
                  extra_headers=extra_headers)


def report_view(client_id, path, language, headers):
    host_name = headers.get('HTTP_HOST', None)
    referrer = headers.get('HTTP_REFERER', None)
    pv = ga.PageView(path, host_name=host_name, referrer=referrer)
    extra_info = ga.SystemInfo(language=language)
    extra_headers = {}
    user_agent = headers.get('HTTP_USER_AGENT', None)
    if user_agent:
        extra_headers['user-agent'] = user_agent
    _report(client_id, pv, extra_info=extra_info, extra_headers=extra_headers)


def report_order(client_id, order):
    for group in order:
        items = [ga.Item(oi.product_name,
                         oi.get_price_per_item(),
                         quantity=oi.quantity,
                         item_id=oi.product_sku)
                 for oi in group]
        trans = ga.Transaction('%s-%s' % (order.id, group.id), items,
                               revenue=group.get_total(),
                               shipping=group.order.shipping_price)
        _report(client_id, trans, {})
