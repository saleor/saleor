from collections import defaultdict
from collections.abc import Iterable

from promise import Promise

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
from .checkout_infos import (
    CheckoutInfoByCheckoutTokenLoader,
    CheckoutLinesInfoByCheckoutTokenLoader,
)


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
                ] = dict(zip(variant_data_list, variant_stocks))
                product_channel_listings_map: dict[
                    tuple[
                        PRODUCT_ID,
                        CHANNEL_SLUG,
                    ],
                    ProductChannelListing,
                ] = dict(zip(product_data_set, product_channel_listings))

                problems = {}

                for checkout_info, lines in zip(checkout_infos, checkout_lines):
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
        line_problems_dataloader = CheckoutLinesProblemsByCheckoutIdLoader(self.context)

        def _resolve_problems(
            checkouts_lines_problems: list[dict[str, list[CHECKOUT_LINE_PROBLEM_TYPE]]],
        ):
            checkout_problems = defaultdict(list)
            for checkout_pk, checkout_lines_problems in zip(
                keys, checkouts_lines_problems
            ):
                checkout_problems[checkout_pk] = get_checkout_problems(
                    checkout_lines_problems
                )

            return [checkout_problems.get(key, []) for key in keys]

        return line_problems_dataloader.load_many(keys).then(_resolve_problems)
