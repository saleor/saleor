from celery import shared_task

from . import api_post_request


@shared_task
def api_post_request_task(transaction_url, data):
    api_post_request(transaction_url, data)
