from ...core.dataloaders import BaseThumbnailBySizeAndFormatLoader


class ThumbnailByAppIdSizeAndFormatLoader(BaseThumbnailBySizeAndFormatLoader):
    context_key = "thumbnail_by_app_size_and_format"
    model_name = "app"


class ThumbnailByAppInstallationIdSizeAndFormatLoader(
    BaseThumbnailBySizeAndFormatLoader
):
    context_key = "thumbnail_by_app_installation_size_and_format"
    model_name = "app_installation"
