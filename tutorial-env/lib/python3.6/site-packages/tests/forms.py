from django.forms import ModelForm

from versatileimagefield.forms import (
    SizedImageCenterpointClickDjangoAdminField, SizedImageCenterpointClickBootstrap3Field
)

from .models import VersatileImageTestModel, VersatileImageWidgetTestModel


class VersatileImageTestModelForm(ModelForm):
    """A form for testing VersatileImageFields."""

    image = SizedImageCenterpointClickDjangoAdminField()
    optional_image = SizedImageCenterpointClickBootstrap3Field()

    class Meta:
        model = VersatileImageTestModel
        fields = (
            'img_type',
            'image',
            'optional_image'
        )


class VersatileImageWidgetTestModelForm(ModelForm):
    """A form for testing VersatileImageField widgets."""

    class Meta:
        model = VersatileImageWidgetTestModel
        fields = ('optional_image_with_ppoi',)
