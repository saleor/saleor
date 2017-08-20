from django.forms import MultiWidget, HiddenInput
from versatileimagefield.widgets import (ClearableFileInputWithImagePreview,
                                         SizedImageCenterpointWidgetMixIn)


class ImagePreviewFileInput(ClearableFileInputWithImagePreview):
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


class ImagePreviewWidget(SizedImageCenterpointWidgetMixIn, MultiWidget):
    def __init__(self, attrs=None):
        widgets = (ImagePreviewFileInput(attrs={'class': 'file-chooser'}),
                   HiddenInput(attrs={'class': 'ppoi-input'}))
        super(ImagePreviewWidget, self).__init__(widgets, attrs)
