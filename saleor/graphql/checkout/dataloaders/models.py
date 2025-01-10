from collections import defaultdict
from collections.abc import Iterable
from uuid import UUID

from django.db.models import F

from ....channel.models import Channel
from ....checkout.models import Checkout, CheckoutLine, CheckoutMetadata
from ....payment.models import TransactionItem
from ...channel.dataloaders import ChannelByIdLoader
from ...core.dataloaders import DataLoader


class CheckoutByTokenLoader(DataLoader[str, Checkout]):
    context_key = "checkout_by_token"

    def batch_load(self, keys):
        checkouts = Checkout.objects.using(self.database_connection_name).in_bulk(keys)
        return [checkouts.get(token) for token in keys]


class CheckoutByUserLoader(DataLoader[int, list[Checkout]]):
    context_key = "checkout_by_user"

    def batch_load(self, keys):
        checkouts = Checkout.objects.using(self.database_connection_name).filter(
            user_id__in=keys, channel__is_active=True
        )
        checkout_by_user_map = defaultdict(list)
        for checkout in checkouts:
            checkout_by_user_map[checkout.user_id].append(checkout)
        return [checkout_by_user_map[user_id] for user_id in keys]


class CheckoutByUserAndChannelLoader(DataLoader[tuple[int, str], list[Checkout]]):
    context_key = "checkout_by_user_and_channel"

    def batch_load(self, keys: Iterable[tuple[int, str]]):
        user_ids = [key[0] for key in keys]
        channel_slugs = [key[1] for key in keys]
        checkouts = (
            Checkout.objects.using(self.database_connection_name)
            .filter(
                user_id__in=user_ids,
                channel__slug__in=channel_slugs,
                channel__is_active=True,
            )
            .annotate(channel_slug=F("channel__slug"))
            .order_by("-last_change", "pk")
        )
        checkout_by_user_and_channel_map = defaultdict(list)
        for checkout in checkouts:
            key = (checkout.user_id, checkout.channel_slug)
            checkout_by_user_and_channel_map[key].append(checkout)
        return [checkout_by_user_and_channel_map[key] for key in keys]


class CheckoutLineByIdLoader(DataLoader[str, CheckoutLine]):
    context_key = "checkout_line_by_id"

    def batch_load(self, keys):
        checkout_lines = CheckoutLine.objects.using(
            self.database_connection_name
        ).in_bulk(keys)
        return [checkout_lines.get(line_id) for line_id in keys]


class CheckoutLinesByCheckoutTokenLoader(DataLoader[str, list[CheckoutLine]]):
    context_key = "checkoutlines_by_checkout"

    def batch_load(self, keys):
        lines = CheckoutLine.objects.using(self.database_connection_name).filter(
            checkout_id__in=keys
        )
        line_map = defaultdict(list)
        for line in lines.iterator():
            line_map[line.checkout_id].append(line)
        return [line_map.get(checkout_id, []) for checkout_id in keys]


class ChannelByCheckoutIDLoader(DataLoader[UUID, Channel]):
    context_key = "channel_by_checkout"

    def batch_load(self, keys):
        def with_checkouts(checkouts):
            def with_channels(channels):
                channel_map = {channel.id: channel for channel in channels}
                return [
                    channel_map.get(checkout.channel_id) if checkout else None
                    for checkout in checkouts
                ]

            channel_ids = {checkout.channel_id for checkout in checkouts if checkout}
            return (
                ChannelByIdLoader(self.context)
                .load_many(channel_ids)
                .then(with_channels)
            )

        return CheckoutByTokenLoader(self.context).load_many(keys).then(with_checkouts)


class CheckoutMetadataByCheckoutIdLoader(DataLoader[str, CheckoutMetadata]):
    context_key = "checkout_metadata_by_checkout_id"

    def batch_load(self, keys):
        checkout_metadata = CheckoutMetadata.objects.using(
            self.database_connection_name
        ).in_bulk(keys, field_name="checkout_id")
        return [checkout_metadata.get(checkout_id) for checkout_id in keys]


class TransactionItemsByCheckoutIDLoader(DataLoader[str, list[TransactionItem]]):
    context_key = "transaction_items_by_checkout_id"

    def batch_load(self, keys):
        transactions = (
            TransactionItem.objects.using(self.database_connection_name)
            .filter(checkout_id__in=keys)
            .order_by("pk")
        )
        transactions_map = defaultdict(list)
        for transaction in transactions:
            transactions_map[transaction.checkout_id].append(transaction)
        return [transactions_map[checkout_id] for checkout_id in keys]
