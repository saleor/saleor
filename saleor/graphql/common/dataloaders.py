from django.conf import settings

from ...warehouse.models import Warehouse
from ..account.dataloaders import AddressByIdLoader
from ..channel.dataloaders import ChannelBySlugLoader
from ..core.dataloaders import DataLoader


class WarehouseCountryCodeByChannelLoader(DataLoader):
    """Loads country code of a first available warehouse that is found for a channel."""

    context_key = "warehouse_country_code_by_channel"

    def batch_load(self, keys):
        def with_channels(channels):
            address_id_by_channel_slug = dict()
            for channel in channels:
                first_warehouse = Warehouse.objects.get_first_warehouse_for_channel(
                    channel.id
                )
                if first_warehouse:
                    address_id_by_channel_slug[
                        channel.slug
                    ] = first_warehouse.address_id

            def with_addresses(addresses):
                address_by_id = {address.pk: address for address in addresses}
                country_codes = []
                for key in keys:
                    address_id = address_id_by_channel_slug.get(key)
                    address = address_by_id.get(address_id) if address_id else None
                    if address and address.country:
                        country_code = address.country.code
                    else:
                        # Fallback when warehouse address has no country set. API has
                        # validation to prevent from adding such addresses, so this is
                        # added only to handle an edge-case if a warehouse would be
                        # added with bypassing the API (for instance with a migration).
                        country_code = settings.DEFAULT_COUNTRY
                    country_codes.append(country_code)
                return country_codes

            address_ids = address_id_by_channel_slug.values()
            return (
                AddressByIdLoader(self.context)
                .load_many(address_ids)
                .then(with_addresses)
            )

        return ChannelBySlugLoader(self.context).load_many(keys).then(with_channels)
