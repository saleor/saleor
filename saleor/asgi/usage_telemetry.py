import asyncio
import hashlib
import json
import logging
import random
import sys

import aiohttp
from asgiref.sync import sync_to_async
from asgiref.typing import (
    ASGI3Application,
    ASGIReceiveCallable,
    ASGISendCallable,
    Scope,
)
from django.apps import apps
from django.conf import settings
from django.db import connections
from django.db.models import Count
from django.utils import timezone

from .. import __version__ as saleor_version
from ..attribute import AttributeEntityType, AttributeInputType, AttributeType

logger = logging.getLogger(__name__)


async def send_usage_telemetry_task():
    if not settings.SEND_USAGE_TELEMETRY:
        return

    # Multiple workers from the same parent process will start almost at the same time.
    # Randomize the start of actual logic to avoid sending data more than once.
    await asyncio.sleep(random.randint(0, 5))

    try:
        data = await sync_to_async(get_usage_telemetry, thread_sensitive=False)()
        if data is None:
            return

        await send_usage_telemetry(data)
    except Exception:
        logger.exception("Sending usage telemetry has failed")

        # Sending usage telemetry data failed, reset the field so during subsequent startup procedure
        # another attempt will be made.
        await sync_to_async(update_usage_telemetry_reported_at, thread_sensitive=False)(
            dt=None, close_connections=True
        )


def get_usage_telemetry():
    """Gather usage telemetry data.

    Data will not be gathered if usage telemetry was recently sent.
    """
    try:
        Site = apps.get_model("sites", "Site")
        site_settings = Site.objects.get_current().settings
        usage_telemetry_reported_at = site_settings.usage_telemetry_reported_at

        cutoff_datetime = timezone.now() - settings.SEND_USAGE_TELEMETRY_AFTER_TIMEDELTA
        if (
            usage_telemetry_reported_at
            and usage_telemetry_reported_at > cutoff_datetime
        ):
            return None

        update_usage_telemetry_reported_at(dt=timezone.now(), close_connections=False)

        instance = {
            "instance_id": str(site_settings.instance_id),
            "saleor_version": saleor_version,
            "python_version": sys.version,
            "is_debug": settings.DEBUG,
            "is_local": isinstance(settings.PUBLIC_URL, str)
            and (
                "localhost" in settings.PUBLIC_URL or "127.0.0.1" in settings.PUBLIC_URL
            ),
        }

        usage = {}

        Product = apps.get_model("product", "Product")
        usage["product_count"] = Product.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).count()

        Attribute = apps.get_model("attribute", "Attribute")
        usage["attribute_count"] = Attribute.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).count()
        usage["attribute_type_count"] = {t[0]: 0 for t in AttributeType.CHOICES}
        for item in (
            Attribute.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
            .values("type")
            .annotate(total=Count("type"))
        ):
            usage["attribute_type_count"][item["type"]] = item["total"]

        usage["attribute_entity_type_count"] = {
            t[0]: 0 for t in AttributeEntityType.CHOICES
        }
        for item in (
            Attribute.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
            .exclude(entity_type__isnull=True)
            .exclude(entity_type="")
            .values("entity_type")
            .annotate(total=Count("entity_type"))
        ):
            usage["attribute_entity_type_count"][item["entity_type"]] = item["total"]

        usage["attribute_input_type_count"] = {
            t[0]: 0 for t in AttributeInputType.CHOICES
        }
        for item in (
            Attribute.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
            .values("input_type")
            .annotate(total=Count("input_type"))
        ):
            usage["attribute_input_type_count"][item["input_type"]] = item["total"]

        AttributePage = apps.get_model("attribute", "AttributePage")
        usage["attribute_page_count"] = AttributePage.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).count()

        AttributeProduct = apps.get_model("attribute", "AttributeProduct")
        usage["attribute_product_count"] = AttributeProduct.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).count()

        AttributeVariant = apps.get_model("attribute", "AttributeVariant")
        usage["attribute_variant_count"] = AttributeVariant.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).count()

        Page = apps.get_model("page", "Page")  # also known as Model
        usage["model_count"] = Page.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).count()

        Channel = apps.get_model("channel", "Channel")
        usage["channel_count"] = Channel.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).count()
        usage["currencies"] = list(
            Channel.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
            .distinct("currency_code")
            .values_list("currency_code", flat=True)
            .order_by("currency_code")
        )

        App = apps.get_model("app", "App")
        usage["saleor_apps"] = list(
            App.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
            .filter(identifier__startswith="saleor.app")
            .values_list("identifier", flat=True)
        )
        usage["app_count"] = App.objects.using(
            settings.DATABASE_CONNECTION_REPLICA_NAME
        ).count()

        return {
            "instance": instance,
            "usage": usage,
            "reported_at": timezone.now().isoformat(timespec="seconds"),
        }
    finally:
        connections.close_all()


async def send_usage_telemetry(data: dict):
    url = "https://usage-telemetry.saleor.io/"

    logger.info("Sending usage telemetry data: %s to: %s", data, url)

    json_data = json.dumps(data)

    headers = {
        "content-type": "application/json",
        # underlying infrastructure requires hash of the data
        "x-amz-content-sha256": hashlib.sha256(json_data.encode("utf-8")).hexdigest(),
    }

    async with aiohttp.ClientSession(
        headers=headers, timeout=aiohttp.ClientTimeout(total=30)
    ) as session:
        async with session.post(url, data=json_data) as resp:
            pass

    return resp.status == 200


def update_usage_telemetry_reported_at(dt, close_connections):
    Site = apps.get_model("sites", "Site")
    try:
        site_settings = Site.objects.get_current().settings
        site_settings.usage_telemetry_reported_at = dt
        site_settings.save(update_fields=["usage_telemetry_reported_at"])
    finally:
        if close_connections:
            connections.close_all()


def usage_telemetry_middleware(application: ASGI3Application) -> ASGI3Application:
    """Send usage telemetry data.

    Saleor does not extract any personal data from your Saleor instance.

    Find more about motivation and how we use this data to improve Saleor at: https://docs.saleor.io/setup/usage-telemetry.
    """

    async def wrapper(
        scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable
    ) -> None:
        if scope.get("type") != "lifespan":
            return await application(scope, receive, send)

        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                try:
                    asyncio.create_task(send_usage_telemetry_task())
                    await send({"type": "lifespan.startup.complete"})
                except Exception as exc:
                    await send({"type": "lifespan.startup.failed", "message": str(exc)})
                    return None
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return None

    return wrapper
