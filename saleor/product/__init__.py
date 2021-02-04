class ProductMediaTypes:
    IMAGE = "image"
    VIDEO_YOUTUBE = "video/youtube"
    VIDEO_UNKNOWN = "video/unknown"

    CHOICES = [
        (IMAGE, "An uploaded image"),
        (VIDEO_YOUTUBE, "A URL to a YouTube video"),
        (VIDEO_UNKNOWN, "A URL to a unknown video provider"),
    ]
