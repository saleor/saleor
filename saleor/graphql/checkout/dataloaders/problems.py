from collections import defaultdict
from collections.abc import Iterable

from promise import Promise

from ....checkout.models import CheckoutDelivery
from ....checkout.problems import (
    CHANNEL_SLUG,
    CHECKOUT_LINE_PROBLEM_TYPE,
    CHECKOUT_PROBLEM_TYPE,
    COUNTRY_CODE,
    PRODUCT_ID,
    VARIANT_ID,
    get_checkout_lines_problems,
    get_checkout_problems,
)
from ....product.models import ProductChannelListing
from ....warehouse.models import Stock
from ...core.dataloaders import DataLoader
from ...product.dataloaders import (
    ProductChannelListingByProductIdAndChannelSlugLoader,
)
from ...warehouse.dataloaders import (
    StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader,
)
from .checkout_delivery import CheckoutDeliveryByIdLoader
from .checkout_infos import (
    CheckoutInfoByCheckoutTokenLoader,
    CheckoutLinesInfoByCheckoutTokenLoader,
)
from .models import CheckoutByTokenLoader


class CheckoutLinesProblemsByCheckoutIdLoader(
    DataLoader[str, dict[str, list[CHECKOUT_LINE_PROBLEM_TYPE]]]
):
    context_key = "checkout_lines_problems_by_checkout_id"

    def batch_load(self, keys):
        stock_dataloader = (
            StocksWithAvailableQuantityByProductVariantIdCountryCodeAndChannelLoader(
                self.context
            )
        )

        def _resolve_problems(data):
            checkout_infos, checkout_lines = data
            variant_data_set: set[
                tuple[
                    VARIANT_ID,
                    CHANNEL_SLUG,
                    COUNTRY_CODE,
                ]
            ] = set()
            product_data_set: set[
                tuple[
                    PRODUCT_ID,
                    CHANNEL_SLUG,
                ]
            ] = set()
            checkout_infos_map = {
                checkout_info.checkout.pk: checkout_info
                for checkout_info in checkout_infos
            }
            for lines in checkout_lines:
                for line in lines:
                    variant_data_set.add(
                        (
                            line.variant.id,
                            line.channel.slug,
                            checkout_infos_map[line.line.checkout_id].checkout.country,
                        )
                    )
                    product_data_set.add(
                        (
                            line.product.id,
                            line.channel.slug,
                        )
                    )
            variant_data_list = list(variant_data_set)
            product_data_list = list(product_data_set)

            def _prepare_problems(data):
                (
                    variant_stocks,
                    product_channel_listings,
                ) = data
                variant_stock_map: dict[
                    tuple[
                        VARIANT_ID,
                        CHANNEL_SLUG,
                        COUNTRY_CODE,
                    ],
                    Iterable[Stock],
                ] = dict(zip(variant_data_list, variant_stocks, strict=False))
                product_channel_listings_map: dict[
                    tuple[
                        PRODUCT_ID,
                        CHANNEL_SLUG,
                    ],
                    ProductChannelListing,
                ] = dict(zip(product_data_set, product_channel_listings, strict=False))

                problems = {}

                for checkout_info, lines in zip(
                    checkout_infos, checkout_lines, strict=False
                ):
                    checkout_id = checkout_info.checkout.pk
                    problems[checkout_id] = get_checkout_lines_problems(
                        checkout_info,
                        lines,
                        variant_stock_map,
                        product_channel_listings_map,
                    )
                return [problems.get(key, []) for key in keys]

            variant_stocks = stock_dataloader.load_many(
                [
                    (variant_id, country_code, channel_slug)
                    for variant_id, channel_slug, country_code in variant_data_list
                ]
            )
            product_channel_listings = (
                ProductChannelListingByProductIdAndChannelSlugLoader(
                    self.context
                ).load_many(product_data_list)
            )

            return Promise.all([variant_stocks, product_channel_listings]).then(
                _prepare_problems
            )

        checkout_infos = CheckoutInfoByCheckoutTokenLoader(self.context).load_many(keys)
        lines = CheckoutLinesInfoByCheckoutTokenLoader(self.context).load_many(keys)
        return Promise.all([checkout_infos, lines]).then(_resolve_problems)


class CheckoutProblemsByCheckoutIdDataloader(
    DataLoader[str, dict[str, list[CHECKOUT_PROBLEM_TYPE]]]
):
    context_key = "checkout_problems_by_checkout_id"

    def batch_load(self, keys):
        def _with_assigned_delivery(checkouts):
            def _resolve_problems(
                data: tuple[
                    list[dict[str, list[CHECKOUT_LINE_PROBLEM_TYPE]]],
                    list[CheckoutDelivery | None],
                ],
            ):
                checkouts_lines_problems, checkouts_deliveries = data
                checkout_problems = defaultdict(list)
                checkout_delivery_map = {
                    delivery.pk: delivery
                    for delivery in checkouts_deliveries
                    if delivery
                }
                for checkout_lines_problems, checkout in zip(
                    checkouts_lines_problems,
                    checkouts,
                    strict=False,
                ):
                    checkout_problems[checkout.pk] = get_checkout_problems(
                        checkout,
                        checkout_delivery_map.get(checkout.assigned_delivery_id),
                        checkout_lines_problems,
                    )

                return [checkout_problems.get(key, []) for key in keys]

            assigned_delivery_ids = [
                checkout.assigned_delivery_id
                for checkout in checkouts
                if checkout.assigned_delivery_id
            ]
            checkout_delivery_dataloader = CheckoutDeliveryByIdLoader(self.context)
            line_problems_dataloader = CheckoutLinesProblemsByCheckoutIdLoader(
                self.context
            )
            return Promise.all(
                [
                    line_problems_dataloader.load_many(keys),
                    checkout_delivery_dataloader.load_many(assigned_delivery_ids),
                ]
            ).then(_resolve_problems)

        return (
            CheckoutByTokenLoader(self.context)
            .load_many(keys)
            .then(_with_assigned_delivery)
        )
