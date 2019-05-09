from .models import VersatileImagePostProcessorTestModel
from ..tests import VersatileImageFieldBaseTestCase


class VersatileImageFieldPostProcessorTestCase(VersatileImageFieldBaseTestCase):

    @classmethod
    def setUpTestData(cls):
        cls.instance = VersatileImagePostProcessorTestModel.objects.create(
            image='python-logo.jpg'
        )

    def test_post_processor(self):
        """
        Ensure versatileimagefield.registry.autodiscover raises the
        appropriate exception when trying to import on versatileimage.py
        modules.
        """
        self.instance.create_on_demand = True
        self.assertEqual(
            self.instance.image.crop['100x100'].url,
            '/media/__sized__/python-logo-2c88a725748e22ee.jpg'
        )

    def test_obscured_file_delete(self):
        self.assertImageDeleted(self.instance.image)
