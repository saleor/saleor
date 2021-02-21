class ProductMediaTypes:
    IMAGE = "image"
    VIDEO = "video"

    CHOICES = [
        (IMAGE, "An uploaded image or an URL to an image"),
        (VIDEO, "A URL to an external video"),
    ]
