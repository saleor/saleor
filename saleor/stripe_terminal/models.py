from django.db import models

class Order(models.Model):
    order_id = models.CharField(max_length=255, blank=True, null=True)
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Order {self.id}"