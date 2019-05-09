from django.contrib import admin
from django.forms import ModelForm

from versatileimagefield.widgets import ClearableFileInputWithImagePreview, VersatileImagePPOISelectWidget

from .models import VersatileImageTestModel, VersatileImageWidgetTestModel


class VersatileImageTestModelForm(ModelForm):

    class Meta:
        model = VersatileImageTestModel
        fields = (
            'image',
            'img_type',
            'optional_image',
            'optional_image_2',
            'optional_image_3'
        )
        widgets = {
            'optional_image': VersatileImagePPOISelectWidget(),
        }


class VersatileImageWidgetTestModelForm(ModelForm):

    class Meta:
        model = VersatileImageWidgetTestModel
        fields = '__all__'
        widgets = {
            'optional_image_2': ClearableFileInputWithImagePreview(),
        }


class VersatileImageTestModelAdmin(admin.ModelAdmin):
    form = VersatileImageTestModelForm


class VersatileImageWidgetTestModelAdmin(admin.ModelAdmin):
    form = VersatileImageWidgetTestModelForm

admin.site.register(VersatileImageTestModel, VersatileImageTestModelAdmin)
admin.site.register(VersatileImageWidgetTestModel, VersatileImageWidgetTestModelAdmin)
