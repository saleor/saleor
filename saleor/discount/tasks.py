from collections import defaultdict
from datetime import datetime
from typing import Dict

import graphene
import pytz
from celery.utils.log import get_task_logger
from django.db.models import F, Q

from ..celeryconf import app
from ..graphql.discount.mutations.utils import CATALOGUE_FIELD_TO_TYPE_NAME
from ..plugins.manager import get_plugins_manager
from .models import Sale
from .utils import CATALOGUE_FIELDS, CatalogueInfo

task_logger = get_task_logger(__name__)


@app.task
def send_sale_toggle_notifications():
    """Send the notification about starting or ending sales."""
    manager = get_plugins_manager()

    sales = get_sales_to_notify_about()

    catalogue_infos = fetch_catalogue_infos(sales)

    if not sales:
        return

    for sale in sales:
        catalogues = catalogue_infos.get(sale.id)
        manager.sale_toggle(sale, catalogues)

    sale_ids = ", ".join([str(sale.id) for sale in sales])
    sales.update(notification_sent_datetime=datetime.now(pytz.UTC))

    task_logger.info("The sale_toggle webhook sent for sales with ids: %s", sale_ids)


def fetch_catalogue_infos(sales):
    catalogue_info: Dict[int, CatalogueInfo] = {}
    for sale_data in sales.values("id", *CATALOGUE_FIELDS):
        sale_id = sale_data["id"]
        if sale_id not in catalogue_info:
            catalogue_info[sale_data["id"]] = defaultdict(set)

        for field in CATALOGUE_FIELDS:
            if id := sale_data.get(field):
                type_name = CATALOGUE_FIELD_TO_TYPE_NAME[field]
                global_id = graphene.Node.to_global_id(type_name, id)
                catalogue_info[sale_data["id"]][field].add(global_id)

    return catalogue_info


def get_sales_to_notify_about():
    """Return sales for which the notify should be sent.

    The notification should be sent for sales for which the start date or end date
    has passed and the notification date is null or the last notification was sent
    before the start or end date.
    """
    now = datetime.now(pytz.UTC)
    sales = Sale.objects.filter(
        (
            (
                Q(notification_sent_datetime__isnull=True)
                | Q(notification_sent_datetime__lt=F("start_date"))
            )
            & Q(start_date__lte=now)
        )
        | (
            (
                Q(notification_sent_datetime__isnull=True)
                | Q(notification_sent_datetime__lt=F("end_date"))
            )
            & Q(end_date__lte=now)
        )
    ).distinct()
    return sales
