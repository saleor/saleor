import uuid

import google_measurement_protocol as ga
from celery import shared_task
from django.conf import settings

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
def ga_report(
        tracking_id, client_id, payloads, extra_headers=None, **extra_data):
    ga.report(
        tracking_id, client_id, payloads, extra_headers=extra_headers,
        **extra_data)


def _report(client_id, payloads, extra_headers=None, **extra_data):
    tracking_id = getattr(settings, 'GOOGLE_ANALYTICS_TRACKING_ID', None)
    if tracking_id and client_id:
        ga_report.delay(
            tracking_id, client_id, payloads, extra_headers=extra_headers,
            **extra_data)


def get_order_payloads(order):
    items = [
        ga.item(
            ol.product_name, ol.unit_price.gross, quantity=ol.quantity,
            item_id=ol.product_sku)
        for ol in order]
    return ga.transaction(
        order.id, items, revenue=order.total.gross, tax=order.total.tax,
        shipping=order.shipping_price.net)


def report_order(client_id, order):
    payloads = get_order_payloads(order)
    _report(client_id, payloads)


def get_view_payloads(path, language, headers):
    host_name = headers.get('HTTP_HOST', None)
    referrer = headers.get('HTTP_REFERER', None)
    return ga.pageview(
        path, host_name=host_name, referrer=referrer, language=language)


def report_view(client_id, path, language, headers):
    payloads = get_view_payloads(path, language, headers)
    extra_headers = {}
    user_agent = headers.get('HTTP_USER_AGENT', None)
    if user_agent:
        extra_headers['user-agent'] = user_agent
    _report(client_id, payloads, extra_headers=extra_headers)
