import json

import graphene
from django.utils.functional import SimpleLazyObject

from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.payloads import generate_meta, generate_requestor


def generate_address_webhook_call_args(address, event, requestor, webhook):
    return [
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Address", address.id),
                "city": address.city,
                "country": {"code": address.country.code, "name": address.country.name},
                "company_name": address.company_name,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: requestor)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        event,
        [webhook],
        address,
        SimpleLazyObject(lambda: requestor),
    ]
