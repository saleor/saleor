from ....celeryconf import app
from ....product.models import Product

from django.db.models import Count, Sum
from django.utils import timezone
from ....channel.models import Channel
from ....graphql.product.filters import filter_products_by_stock_availability
from ....graphql.product.enums import StockAvailability
from ....product.models import Product
from ....order.models import Order
from ....site.models import Statistics


@app.task
def update_statistics_task():
    for channel in Channel.objects.all():
        stats, _ = Statistics.objects.get_or_create(channel=channel)
        today = timezone.now().date()
        orders = Order.objects.filter(created_at__date=today).aggregate(
            total_count=Count("id"), sales_today=Sum("total_charged_amount")
        )
        stats.sales_today = orders["sales_today"] or 0
        stats.orders_today = orders["total_count"] or 0
        stats.orders_to_fulfill = (
            Order.objects.filter(channel=channel).ready_to_fulfill().count()
        )
        stats.orders_to_capture = (
            Order.objects.filter(channel=channel).ready_to_capture().count()
        )
        stats.products_out_of_stock = filter_products_by_stock_availability(
            Product.objects.all(), StockAvailability.OUT_OF_STOCK, channel.slug
        ).count()
        stats.save()
