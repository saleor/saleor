from collections import defaultdict

from ...product.models import ProductMedia
from ..core.dataloaders import DataLoader


class BaseMediaByOwnerIdLoader(DataLoader[int, list[ProductMedia]]):
    """Load a whole gallery for each owner of a given type."""

    owner_field: str

    def batch_load(self, keys):
        media = ProductMedia.objects.using(self.database_connection_name).filter(
            **{f"{self.owner_field}_id__in": keys}
        )
        media_map = defaultdict(list)
        for media_obj in media.iterator(chunk_size=1000):
            media_map[getattr(media_obj, f"{self.owner_field}_id")].append(media_obj)
        return [media_map[owner_id] for owner_id in keys]


class MediaByCategoryIdLoader(BaseMediaByOwnerIdLoader):
    context_key = "media_by_category"
    owner_field = "category"


class MediaByCollectionIdLoader(BaseMediaByOwnerIdLoader):
    context_key = "media_by_collection"
    owner_field = "collection"


class MediaByPageIdLoader(BaseMediaByOwnerIdLoader):
    context_key = "media_by_page"
    owner_field = "page"
