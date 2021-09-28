from typing import Dict


def get_channel_slug_from_filter_data(filter_data: Dict):
    channel = filter_data.get("channel")
    return str(channel) if channel else None
