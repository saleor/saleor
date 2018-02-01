from django.forms import HiddenInput, MultiWidget
from versatileimagefield.widgets import (
    ClearableFileInputWithImagePreview, SizedImageCenterpointWidgetMixIn)


class ImagePreviewFileInput(ClearableFileInputWithImagePreview):
    template_name = 'dashboard/product/product_image/versatile_image.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(
            name, value, attrs)
        value = context['widget']['value']
        if value:
            value.display_value = self.get_filename_from_path(str(value))
        return context

    def get_filename_from_path(self, path):
        filename = path.split('/')[-1]
        return filename if filename else path


class ImagePreviewWidget(SizedImageCenterpointWidgetMixIn, MultiWidget):
    def __init__(self, attrs=None):
        widgets = (ImagePreviewFileInput(attrs={'class': 'file-chooser'}),
                   HiddenInput(attrs={'class': 'ppoi-input'}))
        super().__init__(widgets, attrs)
