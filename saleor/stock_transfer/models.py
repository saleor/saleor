from django.db import models


class StockTransfer(models.Model):
    request_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    approved = models.BooleanField(default=False)
    stock_start = models.CharField(max_length=20)
    stock_target = models.CharField(max_length=20)

    class Meta:
        app_label = "stock_transfer"
