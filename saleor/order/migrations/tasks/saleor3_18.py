from decimal import Decimal
from celery.utils.log import get_task_logger
from django.db.models import Q, F

from ....core.prices import quantize_price
from ....tax.models import TaxConfiguration
from ....channel.models import Channel
from ....order.models import OrderLine, Order
from ....celeryconf import app

task_logger = get_task_logger(__name__)


# Batch size of 700 uses less than 5MB memory, and task took around 1 sec to complete.
LINE_BATCH = 700


def add_taxes_to_price(price, tax_rate, prices_entered_with_tax):
    tax_rate = Decimal(1 + tax_rate)

    if prices_entered_with_tax:
        net_amount = price / tax_rate
        gross_amount = price
    else:
        net_amount = price
        gross_amount = price * tax_rate

    return net_amount, gross_amount


def update_fields_for_line(
    field_name, line, tax_rate, prices_entered_with_tax, lines_to_update
):
    line_net = getattr(line, f"{field_name}_net_amount")
    line_gross = getattr(line, f"{field_name}_gross_amount")
    if line_net == line_gross and all([line_net != 0, line_gross != 0]):
        line_net, line_gross = add_taxes_to_price(
            line_net, tax_rate, prices_entered_with_tax
        )
        setattr(
            line, f"{field_name}_net_amount", quantize_price(line_net, line.currency)
        )
        setattr(
            line,
            f"{field_name}_gross_amount",
            quantize_price(line_gross, line.currency),
        )
        lines_to_update.add(line)


def recalculate_tax_for_prices(
    line, prices_entered_with_tax, tax_rate, lines_to_update
):
    for field in ["undiscounted_unit_price", "undiscounted_total_price"]:
        update_fields_for_line(
            field, line, tax_rate, prices_entered_with_tax, lines_to_update
        )


def get_order_prices_entered_with_tax_mapping(
    order_lines, order_model, channel_model, tax_configuration
):
    orders = order_model.objects.filter(
        id__in=order_lines.values("order_id")
    ).values_list("id", "channel_id")

    channels = channel_model.objects.filter(
        id__in=orders.values("channel_id")
    ).values_list("id")
    tax_configurations = tax_configuration.objects.filter(
        channel_id__in=channels.values("id")
    )
    tax_conf_to_prices_entered_with_taxes = {
        tc_id: price_entered_with_taxes
        for tc_id, price_entered_with_taxes in tax_configurations.values_list(
            "id", "prices_entered_with_tax"
        )
    }

    channel_to_prices_entered_with_taxes = dict()
    for channel_id, tax_conf_id in tax_configurations.values_list("channel_id", "id"):
        channel_to_prices_entered_with_taxes[
            channel_id
        ] = tax_conf_to_prices_entered_with_taxes[tax_conf_id]

    order_to_prices_entered_with_taxes = dict()
    for order_id, channel_id in orders.values_list("id", "channel_id"):
        order_to_prices_entered_with_taxes[
            order_id
        ] = channel_to_prices_entered_with_taxes[channel_id]

    return order_to_prices_entered_with_taxes


@app.task
def recalculate_undiscounted_prices():
    order_lines = (
        OrderLine.objects.filter(
            (
                Q(
                    undiscounted_unit_price_net_amount=F(
                        "undiscounted_unit_price_gross_amount"
                    )
                )
                | Q(
                    undiscounted_total_price_net_amount=F(
                        "undiscounted_total_price_gross_amount"
                    )
                )
            )
            & Q(tax_rate__gt=0)
        )
        .only(
            "pk",
            "undiscounted_unit_price_gross_amount",
            "undiscounted_unit_price_net_amount",
            "undiscounted_total_price_gross_amount",
            "undiscounted_total_price_net_amount",
            "order_id",
            "tax_rate",
            "currency",
        ).order_by("-pk")[:LINE_BATCH]
    )

    if not order_lines:
        task_logger.info("No order lines to update.")
        return
    order_to_prices_with_tax_map = get_order_prices_entered_with_tax_mapping(
        order_lines,
        order_model=Order,
        channel_model=Channel,
        tax_configuration=TaxConfiguration,
    )

    lines_to_update = set()
    for line in order_lines:
        prices_entered_with_tax = order_to_prices_with_tax_map[line.order_id]
        tax_rate = line.tax_rate
        recalculate_tax_for_prices(
            line, prices_entered_with_tax, tax_rate, lines_to_update
        )

    if lines_to_update:
        OrderLine.objects.bulk_update(
            list(lines_to_update),
            [
                "undiscounted_unit_price_gross_amount",
                "undiscounted_unit_price_net_amount",
                "undiscounted_total_price_gross_amount",
                "undiscounted_total_price_net_amount",
            ],
        )

        recalculate_undiscounted_prices.delay()
