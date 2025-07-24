from ...utils.filters import filter_range_field


def filter_updated_at_range(qs, _, value):
    return filter_range_field(qs, "updated_at", value)
