from django.http import HttpResponseNotFound, HttpResponseRedirect
from graphql.error import GraphQLError

from ..graphql.core.utils import from_global_id_or_error
from ..thumbnail import ThumbnailFormat
from ..thumbnail.models import Thumbnail
from .utils import get_thumbnail_size

TYPE_TO_THUMBNAIL_FIELD_MAPPING = {
    "User": "user",
    "Category": "category",
    "Collection": "collection",
    "ProductMedia": "product_media",
}


def handle_thumbnail(request, instance_id: str, size: str, format: str = None):
    """Create and return thumbnail for given instance in provided size and format.

    If the provided size is not in the available resolution list, the thumbnail with
    the closest size is returned or created and returned if it does not exist.
    """
    available_formats = [ThumbnailFormat.WEBP, ThumbnailFormat.AVIF]
    format = format.lower() if format else None
    if format and format not in available_formats:
        return HttpResponseNotFound(
            f"Invalid format value. Available formats: {', '.join(available_formats)}."
        )

    try:
        object_type, pk = from_global_id_or_error(instance_id, raise_error=True)
    except GraphQLError:
        return HttpResponseNotFound("Cannot found instance with the given id.")

    if object_type not in TYPE_TO_THUMBNAIL_FIELD_MAPPING.keys():
        return HttpResponseNotFound("Invalid instance type.")

    size = get_thumbnail_size(size)

    instance_id_lookup = TYPE_TO_THUMBNAIL_FIELD_MAPPING[object_type] + "_id"
    if thumbnail := Thumbnail.objects.filter(
        format=format, size=size, **{instance_id_lookup: pk}
    ).first():
        return HttpResponseRedirect(thumbnail.image.url)

    # TODO: create thumbnail

    # TODO: save thumbnail in models
