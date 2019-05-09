from rest_framework.serializers import ModelSerializer

from versatileimagefield.serializers import VersatileImageFieldSerializer

from .models import VersatileImageTestModel


class VersatileImageTestModelSerializer(ModelSerializer):
    """Serializes VersatileImageTestModel instances"""
    image = VersatileImageFieldSerializer(
        sizes='test_set'
    )
    optional_image = VersatileImageFieldSerializer(
        sizes='test_set'
    )

    class Meta:
        model = VersatileImageTestModel
        exclude = (
            'img_type',
            'height',
            'width',
            'optional_image_2',
            'optional_image_3'
        )
