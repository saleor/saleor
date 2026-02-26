from itertools import chain
from uuid import UUID

from promise import Promise

from ....checkout.delivery_context import get_or_fetch_checkout_deliveries
from ....checkout.models import CheckoutDelivery
from ....core.db.connection import allow_writer_in_context
from ...core.dataloaders import DataLoader
from ...utils import get_user_or_app_from_context
from .checkout_infos import CheckoutInfoByCheckoutTokenLoader


class CheckoutDeliveryByIdLoader(DataLoader[UUID, CheckoutDelivery]):
    context_key = "checkout_delivery_by_id"

    def batch_load(self, keys):
        shipping_methods = CheckoutDelivery.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [shipping_methods.get(key) for key in keys]


class CheckoutDeliveriesByCheckoutIdAndWebhookSyncLoader(
    DataLoader[tuple[UUID, bool], list[CheckoutDelivery]]
):
    context_key = "checkout_deliveries_by_checkout_id_and_webhook_sync_loader"

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        checkout_infos = CheckoutInfoByCheckoutTokenLoader(self.context).load_many(
            [checkout_id for (checkout_id, _) in keys]
        )

        def refresh_delivery_dataloader(
            deliveries: list[list[CheckoutDelivery]],
        ):
            for delivery in chain.from_iterable(deliveries):
                CheckoutDeliveryByIdLoader(self.context).clear(delivery.id)
                CheckoutDeliveryByIdLoader(self.context).prime(delivery.id, delivery)
            return deliveries

        def with_checkout_infos(checkout_infos):
            results = []
            with allow_writer_in_context(self.context):
                for checkout_info, (_, allow_sync_webhooks) in zip(
                    checkout_infos, keys, strict=True
                ):
                    results.append(
                        get_or_fetch_checkout_deliveries(
                            checkout_info=checkout_info,
                            requestor=requestor,
                            allow_sync_webhooks=allow_sync_webhooks,
                        )
                    )
            return Promise.all(results).then(refresh_delivery_dataloader)

        return checkout_infos.then(with_checkout_infos)
