import logging

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse

logger = logging.getLogger(__name__)


def handle_webhook(request: WSGIRequest, gateway_config: "GatewayConfig",
                   channel_slug: str) -> HttpResponse:
    payload = request.body
    logger.info(payload)
    return HttpResponse(status=200)
