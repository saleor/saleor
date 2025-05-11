from graphql.error import GraphQLError
from py_svg_hush import filter_svg


def sanitize_svg(svg_bytes: bytes) -> bytes:
    """Sanitize SVG content to remove any potentially harmful scripts or events."""
    keep_data_url_mime_types = {"image": ["jpeg", "png", "gif"]}
    try:
        return filter_svg(svg_bytes, keep_data_url_mime_types)
    except Exception as e:
        raise GraphQLError("SVG sanitization failed.") from e
