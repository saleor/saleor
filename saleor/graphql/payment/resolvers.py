from ...core.tracing import traced_resolver
from ...payment import models


@traced_resolver
def resolve_payments(info):
    return models.Payment.objects.all()
