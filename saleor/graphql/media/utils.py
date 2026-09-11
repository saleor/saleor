"""Media helpers specific to the GraphQL layer.

Media validation, remote-URL probing and gallery ordering live in
`saleor.product.media`; only presentation concerns belong here.
"""


def sort_media(media, sort_by: dict | None):
    """Sort an already-loaded list of media in Python.

    Media is loaded through a dataloader as a whole gallery, so ordering it here
    avoids a second query per owner.
    """
    if sort_by is None:
        sort_by = {"field": ["sort_order"], "direction": ""}

    def key(media_obj):
        values = tuple(
            getattr(media_obj, field)
            for field in sort_by["field"]
            if getattr(media_obj, field) is not None
        )
        # Nullable values first, achieved by prefixing the number of non-null fields.
        return (len(values), *values)

    return sorted(media, key=key, reverse=sort_by["direction"] == "-")
