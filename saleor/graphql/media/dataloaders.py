from collections import defaultdict

from ...media.models import BaseMedia, CategoryMedia, CollectionMedia, PageMedia
from ..core.dataloaders import BaseThumbnailBySizeAndFormatLoader, DataLoader


class BaseMediaByOwnerIdLoader(DataLoader[int, list[BaseMedia]]):
    """Load a whole gallery for each owner of a given type."""

    model: type[BaseMedia]

    def batch_load(self, keys):
        owner_field = self.model.owner_field
        media = self.model.objects.using(self.database_connection_name).filter(
            **{f"{owner_field}_id__in": keys}
        )
        media_map = defaultdict(list)
        for media_obj in media.iterator(chunk_size=1000):
            media_map[getattr(media_obj, f"{owner_field}_id")].append(media_obj)
        return [media_map[owner_id] for owner_id in keys]


class MediaByCategoryIdLoader(BaseMediaByOwnerIdLoader):
    context_key = "media_by_category"
    model = CategoryMedia


class MediaByCollectionIdLoader(BaseMediaByOwnerIdLoader):
    context_key = "media_by_collection"
    model = CollectionMedia


class MediaByPageIdLoader(BaseMediaByOwnerIdLoader):
    context_key = "media_by_page"
    model = PageMedia


class ThumbnailByCategoryMediaIdSizeAndFormatLoader(BaseThumbnailBySizeAndFormatLoader):
    context_key = "thumbnail_by_categorymedia_size_and_format"
    model_name = "category_media"


class ThumbnailByCollectionMediaIdSizeAndFormatLoader(
    BaseThumbnailBySizeAndFormatLoader
):
    context_key = "thumbnail_by_collectionmedia_size_and_format"
    model_name = "collection_media"


class ThumbnailByPageMediaIdSizeAndFormatLoader(BaseThumbnailBySizeAndFormatLoader):
    context_key = "thumbnail_by_pagemedia_size_and_format"
    model_name = "page_media"
