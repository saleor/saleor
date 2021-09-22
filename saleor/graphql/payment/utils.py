from typing import List


def metadata_contains_empty_key(metadata_list: List[dict]) -> bool:
    return not all([data["key"].strip() for data in metadata_list])
