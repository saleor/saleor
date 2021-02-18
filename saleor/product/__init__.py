class ProductMediaTypes:
    IMAGE = "image"
    VIDEO_YOUTUBE = "video/youtube"
    VIDEO_STREAMABLE = "video/streamable"
    VIDEO_VIMEO = "video/vimeo"

    CHOICES = [
        (IMAGE, "An uploaded image"),
        (VIDEO_YOUTUBE, "A URL to a YouTube video"),
        (VIDEO_STREAMABLE, "A URL to a Streamable video"),
        (VIDEO_VIMEO, "A URL to a Vimeo video"),
    ]
