from collections.abc import Iterable
from uuid import UUID

from promise import Promise

from ....app.models import App
from ....checkout.calculations import fetch_checkout_data
from ....checkout.fetch import CheckoutInfo, CheckoutLineInfo
from ...app.dataloaders.utils import get_app_promise
from ...core.dataloaders import DataLoader
from ...plugins.dataloaders import plugin_manager_promise
from .checkout_infos import (
    CheckoutInfoByCheckoutTokenLoader,
    CheckoutLinesInfoByCheckoutTokenLoader,
)


class CheckoutPriceCalculationByCheckoutIdAndWebhookSyncAndForceStatusUpdateLoader(
    DataLoader[tuple[UUID, bool, bool], tuple[CheckoutInfo, list[CheckoutLineInfo]]]
):
    context_key = (
        "checkout_price_calculation_by_checkout_id_and_webhook_sync_and_status"
    )

    def batch_load(
        self, keys: Iterable[tuple[UUID, bool, bool]]
    ) -> Promise[list[tuple[CheckoutInfo, list[CheckoutLineInfo]]]]:
        tokens = [token for (token, _, _) in keys]
        lines_dataloader = CheckoutLinesInfoByCheckoutTokenLoader(
            self.context
        ).load_many(keys=tokens)
        checkout_info_dataloader = CheckoutInfoByCheckoutTokenLoader(
            self.context
        ).load_many(keys=tokens)

        def with_checkout_details(
            data: tuple[App | None, list[CheckoutInfo], list[list[CheckoutLineInfo]]],
        ):
            app, checkout_infos, line_infos = data

            def calculate_prices(manager):
                results: list[Promise[tuple[CheckoutInfo, list[CheckoutLineInfo]]]] = []
                for checkout_info, lines_info, (
                    _,
                    allow_sync_webhooks,
                    force_status_update,
                ) in zip(checkout_infos, line_infos, keys, strict=True):
                    result = fetch_checkout_data(
                        checkout_info=checkout_info,
                        manager=manager,
                        lines=lines_info,
                        requestor=app or self.context.user,
                        database_connection_name=self.database_connection_name,
                        allow_sync_webhooks=allow_sync_webhooks,
                        force_status_update=force_status_update,
                    )
                    results.append(result)
                return Promise.all(results)

            return plugin_manager_promise(self.context, app).then(calculate_prices)

        return Promise.all(
            [get_app_promise(self.context), checkout_info_dataloader, lines_dataloader]
        ).then(with_checkout_details)
