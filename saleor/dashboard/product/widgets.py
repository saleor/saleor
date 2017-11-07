from django.forms import MultiWidget, HiddenInput
from versatileimagefield.widgets import (ClearableFileInputWithImagePreview,
                                         SizedImageCenterpointWidgetMixIn)


class ImagePreviewFileInput(ClearableFileInputWithImagePreview):
    template_name = 'dashboard/product/product_image/versatile_image.html'
    template_with_initial_and_imagepreview = """
    <div class="sizedimage-mod preview">
        <div class="image-wrap outer">
            <div class="point-stage" id="%(point_stage_id)s"
                 data-image_preview_id="%(image_preview_id)s">
                <div class="ppoi-point" id="%(ppoi_id)s"></div>
            </div>
            <div class="image-wrap inner">
                %(image_preview)s
            </div>
        </div>
    </div>"""

    def get_context(self, name, value, attrs):
        context = super(ImagePreviewFileInput, self).get_context(
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
        super(ImagePreviewWidget, self).__init__(widgets, attrs)
