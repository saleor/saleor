from typing import Dict


def get_channel_slug_from_filter_data(filter_data: Dict):
    channel_slug = str(filter_data["channel"])
    return channel_slug
