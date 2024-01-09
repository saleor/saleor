def get_channel_slug_from_filter_data(filter_data: dict):
    channel = filter_data.get("channel")
    return str(channel) if channel else None


def get_currency_from_filter_data(filter_data: dict):
    currency = filter_data.get("currency")
    return str(currency) if currency else None
