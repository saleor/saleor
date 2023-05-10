from ..celeryconf import app
from .models import Statistics


@app.task
def nullify_todays_stats():
    Statistics.objects.update(orders_today=0, sales_today=0)
