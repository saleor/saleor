from collections import defaultdict
from uuid import UUID

from promise import Promise

from ....discount.interface import VariantPromotionRuleInfo
from ...core.dataloaders import DataLoader
from ...discount.dataloaders import (
    PromotionByRuleIdLoader,
    PromotionRuleByIdLoader,
)
from ...product.dataloaders import (
    VariantChannelListingByVariantIdAndChannelIdLoader,
    VariantChannelListingPromotionRuleByListingIdLoader,
)
from ...translations.dataloaders import (
    PromotionRuleTranslationByIdAndLanguageCodeLoader,
    PromotionTranslationByIdAndLanguageCodeLoader,
)
from .models import CheckoutByTokenLoader, CheckoutLineByIdLoader


class VariantPromotionRuleInfoByCheckoutLineIdLoader(
    DataLoader[UUID, list[VariantPromotionRuleInfo]]
):
    context_key = "variant_promotion_rule_info_by_checkout_line_id"

    def batch_load(self, keys):
        def with_checkout_lines(checkout_lines):
            def with_checkouts(checkouts):
                variants_pks = [line.variant_id for line in checkout_lines]
                if not variants_pks:
                    return []

                channel_pks = [checkout.channel_id for checkout in checkouts]

                def with_channel_listings(channel_listings):
                    def with_channel_listing_promotion_rules(
                        variant_listing_promotion_rules,
                    ):
                        rule_ids: list[int] = []
                        rule_ids_language_codes: list[tuple[int, str]] = []
                        for listing_promotion_rules, language_code in zip(
                            variant_listing_promotion_rules, language_codes
                        ):
                            for listing_promotion_rule in listing_promotion_rules:
                                rule_ids.append(
                                    listing_promotion_rule.promotion_rule_id
                                )
                                rule_ids_language_codes.append(
                                    (
                                        listing_promotion_rule.promotion_rule_id,
                                        language_code,
                                    )
                                )

                        def with_promotion_rules(results):
                            promotion_rules, promotions, rule_translations = results

                            promotion_ids_language_codes = [
                                (rule.promotion_id, language_code)
                                for rule, (_rule_id, language_code) in zip(
                                    promotion_rules, rule_ids_language_codes
                                )
                            ]

                            def with_promotion_translations(promotion_translations):
                                channel_listings_map = dict(
                                    zip(variant_ids_channel_ids, channel_listings)
                                )
                                listing_promotion_rules_map = dict(
                                    zip(
                                        channel_listing_ids,
                                        variant_listing_promotion_rules,
                                    )
                                )
                                rule_map = dict(zip(rule_ids, promotion_rules))
                                rule_id_to_promotion_map = dict(
                                    zip(rule_ids, promotions)
                                )
                                rule_id_to_rule_translation = dict(
                                    zip(rule_ids, rule_translations)
                                )
                                rule_id_to_promotion_translation = dict(
                                    zip(rule_ids, promotion_translations)
                                )

                                rules_info_map = defaultdict(list)
                                for checkout, line in zip(checkouts, checkout_lines):
                                    channel_listing = channel_listings_map[
                                        (line.variant_id, checkout.channel_id)
                                    ]
                                    listing_promotion_rules = (
                                        listing_promotion_rules_map[channel_listing.id]
                                        if channel_listing
                                        else []
                                    )
                                    rules_info_map[line.id] = [
                                        VariantPromotionRuleInfo(
                                            rule=rule_map[
                                                listing_rule.promotion_rule_id
                                            ],
                                            variant_listing_promotion_rule=listing_rule,
                                            promotion=rule_id_to_promotion_map[
                                                listing_rule.promotion_rule_id
                                            ],
                                            rule_translation=rule_id_to_rule_translation[
                                                listing_rule.promotion_rule_id
                                            ],
                                            promotion_translation=rule_id_to_promotion_translation[
                                                listing_rule.promotion_rule_id
                                            ],
                                        )
                                        for listing_rule in listing_promotion_rules
                                    ]

                                return [rules_info_map[key] for key in keys]

                            return (
                                PromotionTranslationByIdAndLanguageCodeLoader(
                                    self.context
                                )
                                .load_many(promotion_ids_language_codes)
                                .then(with_promotion_translations)
                            )

                        promotion_rules = PromotionRuleByIdLoader(
                            self.context
                        ).load_many(rule_ids)
                        promotions = PromotionByRuleIdLoader(self.context).load_many(
                            rule_ids
                        )

                        rules_translations = (
                            PromotionRuleTranslationByIdAndLanguageCodeLoader(
                                self.context
                            ).load_many(rule_ids_language_codes)
                        )
                        return Promise.all(
                            [promotion_rules, promotions, rules_translations]
                        ).then(with_promotion_rules)

                    channel_listing_ids = [
                        listing.id for listing in channel_listings if listing
                    ]
                    return (
                        VariantChannelListingPromotionRuleByListingIdLoader(
                            self.context
                        )
                        .load_many(channel_listing_ids)
                        .then(with_channel_listing_promotion_rules)
                    )

                variant_ids_channel_ids = [
                    (line.variant_id, channel_id)
                    for line, channel_id in zip(checkout_lines, channel_pks)
                ]
                language_codes = [checkout.language_code for checkout in checkouts]

                return (
                    VariantChannelListingByVariantIdAndChannelIdLoader(self.context)
                    .load_many(variant_ids_channel_ids)
                    .then(with_channel_listings)
                )

            checkout_tokens = [line.checkout_id for line in checkout_lines]
            return (
                CheckoutByTokenLoader(self.context)
                .load_many(checkout_tokens)
                .then(with_checkouts)
            )

        return (
            CheckoutLineByIdLoader(self.context)
            .load_many(keys)
            .then(with_checkout_lines)
        )
