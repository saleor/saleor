"""versatileimagefield tests."""
from __future__ import division, unicode_literals

from functools import reduce
import math
import operator
import os
from shutil import rmtree

from django.conf import settings
from django.contrib.auth.models import User
from django.core import serializers
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import get_template
from django.test import TestCase
from django.test.utils import override_settings
from django.utils._os import upath
from django.utils.six.moves import cPickle

from PIL import Image
from rest_framework.test import APIRequestFactory

from versatileimagefield.datastructures.base import ProcessedImage
from versatileimagefield.datastructures.filteredimage import InvalidFilter
from versatileimagefield.datastructures.sizedimage import MalformedSizedImageKey, SizedImage
from versatileimagefield.datastructures.filteredimage import FilteredImage
from versatileimagefield.image_warmer import VersatileImageFieldWarmer
from versatileimagefield.registry import (
    autodiscover, versatileimagefield_registry, AlreadyRegistered, InvalidSizedImageSubclass,
    InvalidFilteredImageSubclass, NotRegistered, UnallowedSizerName, UnallowedFilterName
)
from versatileimagefield.settings import (
    QUAL, VERSATILEIMAGEFIELD_SIZED_DIRNAME, VERSATILEIMAGEFIELD_FILTERED_DIRNAME,
    VERSATILEIMAGEFIELD_PLACEHOLDER_DIRNAME
)
from versatileimagefield.utils import (
    get_filtered_filename,
    get_rendition_key_set,
    get_resized_filename,
    InvalidSizeKey,
    InvalidSizeKeySet
)
from versatileimagefield.validators import validate_ppoi_tuple
from versatileimagefield.versatileimagefield import CroppedImage, InvertImage

from .forms import VersatileImageTestModelForm, VersatileImageWidgetTestModelForm
from .models import (
    VersatileImageTestModel,
    VersatileImageTestUploadDirectoryModel,
    VersatileImageWidgetTestModel,
    MaybeVersatileImageModel
)
from .serializers import VersatileImageTestModelSerializer

try:
    from django.core.urlresolvers import reverse
except ImportError:  # Django >= 1.10
    from django.urls import reverse


class VersatileImageFieldBaseTestCase(TestCase):
    """Base test case for versatileimagefield."""

    @classmethod
    def tearDownClass(cls):
        """Delete files made by VersatileImageFields during tests."""
        filtered_path = os.path.join(
            settings.MEDIA_ROOT,
            VERSATILEIMAGEFIELD_FILTERED_DIRNAME
        )
        sized_path = os.path.join(
            settings.MEDIA_ROOT,
            VERSATILEIMAGEFIELD_SIZED_DIRNAME
        )
        placeholder_path = os.path.join(
            settings.MEDIA_ROOT,
            VERSATILEIMAGEFIELD_PLACEHOLDER_DIRNAME
        )
        rmtree(filtered_path, ignore_errors=True)
        rmtree(sized_path, ignore_errors=True)
        rmtree(placeholder_path, ignore_errors=True)

    def assertImageDeleted(self, field_instance):
        """Assert `field_instance` (VersatileImageField instance) deletes."""
        img_url = field_instance.crop['100x100'].url
        self.assertEqual(cache.get(img_url), None)
        field_instance.create_on_demand = True
        field_instance.crop['100x100'].url
        self.assertEqual(cache.get(img_url), 1)
        self.assertTrue(
            field_instance.field.storage.exists(
                field_instance.crop['100x100'].name
            )
        )
        field_instance.field.storage.delete(field_instance.crop['100x100'].name)
        self.assertFalse(
            field_instance.field.storage.exists(
                field_instance.crop['100x100'].name
            )
        )
        cache.delete(img_url)
        self.assertEqual(cache.get(img_url), None)
        field_instance.create_on_demand = False


class VersatileImageFieldTestCase(VersatileImageFieldBaseTestCase):
    """Main test case for versatileimagefield."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username='test',
            email='test@test.com',
            password='12345',
        )
        cls.jpg = VersatileImageTestModel.objects.create(
            img_type='jpg',
            image="python-logo.jpg",
            ppoi="0.25x0.25",
            width=0,
            height=0
        )
        cls.png = VersatileImageTestModel.objects.create(
            img_type='png',
            image="python-logo.png",
            optional_image="python-logo.jpg",
            ppoi="0.5x0.5",
            width=0,
            height=0
        )
        cls.gif = VersatileImageTestModel.objects.create(
            img_type='gif',
            image="python-logo.gif",
            ppoi="0.75x0.75",
            width=0,
            height=0
        )
        cls.delete_test = VersatileImageTestModel.objects.create(
            img_type='delete_test',
            image="delete-test/python-logo-delete-test.jpg",
            ppoi="0.5x0.5",
            width=0,
            height=0
        )
        cls.widget_test = VersatileImageWidgetTestModel.objects.create(
            image="python-logo.png",
            image_no_ppoi="python-logo.jpg",
            optional_image="exif-orientation-examples/Landscape_8.jpg",
            optional_image_with_ppoi="exif-orientation-examples/Landscape_6.jpg",
            ppoi="0.5x0.5",
            optional_image_with_ppoi_ppoi="1.0x1.0",
            required_text_field="boo urns"
        )
        cls.admin_url = reverse('admin:tests_versatileimagewidgettestmodel_change', args=(cls.widget_test.pk,))

    def setUp(self):
        """Build test instances, create test client."""
        self.client.login(username='test', password='12345')

    def assertImageEqual(self, image1, image2):
        """Assert that `image1` & `image2` are identical images."""
        h1 = image1.histogram()
        h2 = image2.histogram()
        rms = math.sqrt(
            reduce(
                operator.add,
                map(lambda a, b: (a - b) ** 2, h1, h2)
            ) // len(h1)
        )
        self.assertEqual(rms, 0.0)

    def test_field_can_be_null(self):
        obj = MaybeVersatileImageModel(pk=34, name='foo')
        obj.save()

    def test_storage_fails_to_return_url(self):
        """
        This is a wonky test used to ensure 100% code coverge in utils.py.

        We need to test that a storage.url call can hit an exception to trigger
        resized_url = None in try/except
        """
        import types
        from copy import deepcopy
        from django.utils.six import BytesIO

        def storage_url_fail(self, path):
            if self.exists(path):
                return path

            raise Exception("Storage class returns exception because file does not exist.")

        class SizedImageSubclass(SizedImage):
            filename_key = 'test'

            def process_image(self, image, image_format, save_kwargs, width, height):
                return BytesIO()

        _storage = deepcopy(self.jpg.image.field.storage)
        _storage.url = types.MethodType(storage_url_fail, _storage)

        s = SizedImageSubclass(self.jpg.image.name, _storage, True)
        s['100x100']

    def test_check_storage_paths(self):
        """Ensure storage paths are properly set."""
        self.assertEqual(self.jpg.image.name, 'python-logo.jpg')
        self.assertEqual(self.png.image.name, 'python-logo.png')
        self.assertEqual(self.gif.image.name, 'python-logo.gif')

    def test_thumbnail_resized_path(self):
        """Ensure thumbnail Sizer paths are set correctly."""
        self.assertEqual(
            self.jpg.image.thumbnail['100x100'].url,
            '/media/__sized__/python-logo-thumbnail-100x100-70.jpg'
        )

    def test_crop_resized_path(self):
        """Ensure crop Sizer paths are set correctly."""
        self.assertEqual(
            self.jpg.image.crop['100x100'].url,
            '/media/__sized__/python-logo-crop-c0-25__0-25-100x100-70.jpg'
        )
        self.assertEqual(
            self.gif.image.crop['100x100'].url,
            '/media/__sized__/python-logo-crop-c0-75__0-75-100x100.gif'
        )
        self.assertEqual(
            self.png.image.crop['100x100'].url,
            '/media/__sized__/python-logo-crop-c0-5__0-5-100x100.png'
        )

    def test_invert_filtered_path(self):
        """Ensure crop Sizer paths are set correctly."""
        self.assertEqual(
            self.jpg.image.filters.invert.url,
            '/media/__filtered__/python-logo__invert__.jpg'
        )

    def test_invalid_filter(self):
        """Ensure InvalidFilter raises."""
        with self.assertRaises(InvalidFilter):
            invalid_filter = self.jpg.image.filters.non_existant.url
            del invalid_filter

    def test_invert_plus_thumbnail_sizer_filtered_path(self):
        """Ensure crop Sizer paths are set correctly."""
        self.assertEqual(
            self.jpg.image.filters.invert.thumbnail['100x100'].url,
            (
                '/media/__sized__/__filtered__/python-logo__invert__'
                '-thumbnail-100x100-70.jpg'
            )
        )

    def test_placeholder_image(self):
        """Ensure placeholder images work as intended."""
        self.jpg.optional_image.create_on_demand = True
        self.assertEqual(
            self.jpg.optional_image.url,
            '/media/__placeholder__/placeholder.png'
        )
        self.assertEqual(
            self.jpg.optional_image.crop['100x100'].url,
            '/media/__sized__/__placeholder__/'
            'placeholder-crop-c0-5__0-5-100x100.png'
        )
        self.assertEqual(
            self.jpg.optional_image.thumbnail['100x100'].url,
            '/media/__sized__/__placeholder__/'
            'placeholder-thumbnail-100x100.png'
        )
        self.assertEqual(
            self.jpg.optional_image.filters.invert.url,
            '/media/__placeholder__/__filtered__/placeholder__invert__.png'
        )
        self.assertEqual(
            self.jpg.optional_image_2.crop['100x100'].url,
            '/media/__sized__/__placeholder__/on-storage-placeholder/'
            'placeholder-crop-c0-5__0-5-100x100.png'
        )
        self.assertEqual(
            self.jpg.optional_image_2.thumbnail['100x100'].url,
            '/media/__sized__/__placeholder__/on-storage-placeholder/'
            'placeholder-thumbnail-100x100.png'
        )
        self.assertEqual(
            self.jpg.optional_image_2.filters.invert.url,
            '/media/__placeholder__/on-storage-placeholder/__filtered__/'
            'placeholder__invert__.png'
        )
        self.assertFalse(
            self.jpg.optional_image.field.storage.size(
                self.jpg.optional_image.name
            ) is 0
        )
        self.jpg.optional_image.create_on_demand = False

    def test_setting_ppoi_values(self):
        """Ensure PPOI values are set correctly."""
        self.jpg.image.ppoi = (0.5, 0.5)
        self.assertEqual(self.jpg.image.ppoi, (0.5, 0.5))

        self.jpg.image.ppoi = '0.25x0.25'
        self.assertEqual(self.jpg.image.ppoi, (0.25, 0.25))

        with self.assertRaises(ValidationError):
            image = self.jpg.image
            image.ppoi = (1.5, 2)

        with self.assertRaises(ValidationError):
            image = self.jpg.image
            image.ppoi = 'picklexcucumber'

    def test_invalid_ppoi_tuple_validation(self):
        """Ensure validate_ppoi_tuple works as expected."""
        self.assertFalse(validate_ppoi_tuple((0, 1.5, 6)))

    def test_create_on_demand_boolean(self):
        """Ensure create_on_demand boolean is set appropriately."""
        self.jpg.image.create_on_demand = False
        self.assertFalse(self.jpg.image.create_on_demand)
        self.jpg.image.create_on_demand = True
        self.assertTrue(self.jpg.image.create_on_demand)
        self.jpg.image.create_on_demand = False

        with self.assertRaises(ValueError):
            self.jpg.image.create_on_demand = 'pickle'

    def test_create_on_demand_functionality(self):
        """Ensure create_on_demand functionality works as advertised."""
        self.assertImageDeleted(self.jpg.image)

    def test_custom_upload_to_thumbnail_deleted(self):
        """Test custom upload_to deletion works."""
        o = VersatileImageTestUploadDirectoryModel.objects.create(image="foo/python-logo.jpg")
        field_instance = o.image
        field_instance.create_on_demand = True
        path = field_instance.crop['100x100'].name
        self.assertTrue(field_instance.field.storage.exists(path))
        field_instance.delete_sized_images()
        self.assertFalse(field_instance.field.storage.exists(path))

    def test_image_warmer(self):
        """Ensure VersatileImageFieldWarmer works as advertised."""
        jpg_warmer = VersatileImageFieldWarmer(
            instance_or_queryset=self.jpg,
            rendition_key_set='test_set',
            image_attr='image'
        )
        num_created, failed_to_create = jpg_warmer.warm()
        self.assertEqual(num_created, 5)
        all_imgs_warmer = VersatileImageFieldWarmer(
            instance_or_queryset=VersatileImageTestModel.objects.exclude(
                img_type='delete_test'
            ),
            rendition_key_set=(
                ('test_thumb', 'thumbnail__100x100'),
                ('test_crop', 'crop__100x100'),
                ('test_invert', 'filters__invert__url'),
            ),
            image_attr='image',
            verbose=True
        )
        num_created, failed_to_create = all_imgs_warmer.warm()

        with self.assertRaises(ValueError):
            invalid_warmer = VersatileImageFieldWarmer(
                instance_or_queryset=['invalid'],
                rendition_key_set=(
                    ('test_thumb', 'thumbnail__10x10'),
                ),
                image_attr='image'
            )
            del invalid_warmer

    def test_versatile_image_field_serializer_output(self):
        """Ensure VersatileImageFieldSerializer serializes correctly."""
        serializer = VersatileImageTestModelSerializer(
            self.jpg,
            context={'request': APIRequestFactory().get('/admin/')}
        )
        self.assertEqual(
            serializer.data.get('image'),
            {
                'test_crop': 'http://testserver/media/__sized__/python-logo-crop-c0-25__0-25-100x100-70.jpg',
                'test_invert_crop': 'http://testserver/media/__sized__/__filtered__/python-logo__invert__-crop-c0-25__0-25-100x100-70.jpg',
                'test_invert_thumb': 'http://testserver/media/__sized__/__filtered__/python-logo__invert__-thumbnail-100x100-70.jpg',
                'test_invert': 'http://testserver/media/__filtered__/python-logo__invert__.jpg',
                'test_thumb': 'http://testserver/media/__sized__/python-logo-thumbnail-100x100-70.jpg',
            }
        )
        self.assertEqual(
            serializer.data.get('optional_image'),
            {
                'test_crop': 'http://testserver/media/__sized__/__placeholder__/placeholder-crop-c0-5__0-5-100x100.png',
                'test_invert_crop': 'http://testserver/media/__sized__/__placeholder__/__filtered__/placeholder__invert__-crop-c0-5__0-5-100x100.png',
                'test_invert_thumb': 'http://testserver/media/__sized__/__placeholder__/__filtered__/placeholder__invert__-thumbnail-100x100.png',
                'test_invert': 'http://testserver/media/__placeholder__/__filtered__/placeholder__invert__.png',
                'test_thumb': 'http://testserver/media/__sized__/__placeholder__/placeholder-thumbnail-100x100.png',
            }
        )

    def test_widget_javascript(self):
        """Ensure VersatileImagePPOIClickWidget widget loads appropriately."""
        self.widget_test.image.create_on_demand = True
        self.widget_test.image.url

        self.widget_test.optional_image.create_on_demand = True
        self.widget_test.optional_image.url

        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 200)
        # Test that javascript loads correctly
        self.assertContains(
            response,
            '<script type="text/javascript" src="/static/versatileimagefield/js/versatileimagefield.js"></script>',
            html=True
        )

        # Test required field with PPOI
        self.assertContains(
            response,
            """
            <div class="image-wrap outer">
              <div class="point-stage" id="image_0_point-stage"
                   data-image_preview_id="image_0_imagepreview">
                <div class="ppoi-point" id="image_0_ppoi"></div>
              </div>
              <div class="image-wrap inner">
                <img src="/media/__sized__/python-logo-thumbnail-300x300.png"
                     id="image_0_imagepreview"
                     data-hidden_field_id="id_image_1"
                     data-point_stage_id="image_0_point-stage"
                     data-ppoi_id="image_0_ppoi" class="sizedimage-preview"/>
              </div>
            </div>
            """,
            html=True
        )

        # Test required field no PPOI
        self.assertContains(
            response,
            '<a href="/media/python-logo.jpg">python-logo.jpg</a>',
        )

        # Test optional image no PPOI
        self.assertContains(
            response,
            """
            <a href="/media/exif-orientation-examples/Landscape_8.jpg">exif-orientation-examples/Landscape_8.jpg</a>
            """,
            html=True
        )

        # Test optional image with PPOI
        self.assertContains(
            response,
            """
            <div class="versatileimagefield">
              <div class="sizedimage-mod initial">
                <label class="versatileimagefield-label">Currently</label>
                <a href="/media/exif-orientation-examples/Landscape_6.jpg">
                  exif-orientation-examples/Landscape_6.jpg
                </a>
              </div>
              <div class="sizedimage-mod clear">
                <input id="optional_image_with_ppoi_0-clear_id"
                       name="optional_image_with_ppoi_0-clear" type="checkbox" />
                <label class="versatileimagefield-label" for="optional_image_with_ppoi_0-clear_id">
                  Clear:
                </label>
              </div>
              <div class="sizedimage-mod preview">
                <label class="versatileimagefield-label">
                  Primary Point of Interest
                </label>
                <div class="image-wrap outer">
                  <div class="point-stage"
                       id="optional_image_with_ppoi_0_point-stage"
                       data-image_preview_id="optional_image_with_ppoi_0_imagepreview">
                    <div class="ppoi-point" id="optional_image_with_ppoi_0_ppoi"></div>
                  </div>
                  <div class="image-wrap inner">
                    <img src="/media/__sized__/exif-orientation-examples/Landscape_6-thumbnail-300x300-70.jpg"
                         id="optional_image_with_ppoi_0_imagepreview"
                         data-hidden_field_id="id_optional_image_with_ppoi_1"
                         data-point_stage_id="optional_image_with_ppoi_0_point-stage"
                         data-ppoi_id="optional_image_with_ppoi_0_ppoi" class="sizedimage-preview"/>
                  </div>
                </div>
              </div>
              <div class="sizedimage-mod new-upload">
                <label class="versatileimagefield-label">Change</label>
                <input class="file-chooser" id="id_optional_image_with_ppoi_0"
                       name="optional_image_with_ppoi_0" type="file" />
              </div>
              <input class="ppoi-input" id="id_optional_image_with_ppoi_1"
                     name="optional_image_with_ppoi_1" type="hidden" value="1.0x1.0" />
            </div>
            """,
            html=True
        )
        self.assertTrue(
            self.png.image.field.storage.exists(
                self.png.image.thumbnail['300x300'].name
            )
        )
        form = VersatileImageWidgetTestModelForm(
            data={
                'optional_image_with_ppoi_0': '',
                'optional_image_with_ppoi_0-clear': 'on'
            },
            instance=self.widget_test
        )
        instance = form.save(commit=False)
        self.assertEqual(instance.optional_image_with_ppoi.name, '')

    def test_versatile_image_field_picklability(self):
        """Ensure VersatileImageField instances can be pickled/unpickled."""
        cPickle.dump(self.jpg, open("pickletest.p", "wb"))
        jpg_unpickled = cPickle.load(open("pickletest.p", "rb"))
        jpg_instance = jpg_unpickled
        self.assertEqual(
            jpg_instance.image.thumbnail['100x100'].url,
            '/media/__sized__/python-logo-thumbnail-100x100-70.jpg'
        )
        pickled_state = self.jpg.image.__getstate__()
        self.assertEqual(
            pickled_state,
            {
                '_create_on_demand': False,
                '_committed': True,
                '_file': None,
                'name': 'python-logo.jpg',
                'closed': False
            }
        )

    def test_versatile_image_field_rendition_key_sets_setting(self):
        """Ensure VERSATILEIMAGEFIELD_RENDITION_KEY_SETS setting validates."""
        with self.assertRaises(ImproperlyConfigured):
            get_rendition_key_set('does_not_exist')

        with self.assertRaises(InvalidSizeKeySet):
            get_rendition_key_set('invalid_set')

        with self.assertRaises(InvalidSizeKey):
            get_rendition_key_set('invalid_size_key')

    def test_exif_orientation_rotate_180(self):
        """Ensure exif orientation==3 data processes properly."""
        exif_3 = VersatileImageTestModel.objects.create(
            img_type='exif_3',
            image="exif-orientation-examples/Landscape_3.jpg",
            ppoi="0.5x0.5",
            width=0,
            height=0
        )
        exif_3.image.create_on_demand = True
        exif_3_path = exif_3.image.thumbnail['100x100'].name
        # exif_3_img = exif_3.image.field.storage.open(exif_3_path)
        # exif_3_control = exif_3.image.field.storage.open(
        #    'verify-against/exif-orientation-examples/Landscape_3-thumbnail-100x100.jpg'
        # )
        # self.assertImageEqual(Image.open(exif_3_img), Image.open(exif_3_control))

    def test_exif_orientation_rotate_270(self):
        """Ensure exif orientation==6 data processes properly."""
        exif_6 = VersatileImageTestModel.objects.create(
            img_type='exif_6',
            image="exif-orientation-examples/Landscape_6.jpg",
            ppoi="0.5x0.5",
            width=0,
            height=0
        )
        exif_6.image.create_on_demand = True
        exif_6_path = exif_6.image.thumbnail['100x100'].name
        # exif_6_img = exif_6.image.field.storage.open(exif_6_path)
        # exif_6_control = exif_6.image.field.storage.open(
        #     'verify-against/exif-orientation-examples/Landscape_6-thumbnail-100x100.jpg'
        # )
        # self.assertImageEqual(
        #     Image.open(exif_6_img),
        #     Image.open(exif_6_control)
        # )

    def test_exif_orientation_rotate_90(self):
        """Ensure exif orientation==8 data processes properly."""
        exif_8 = VersatileImageTestModel.objects.create(
            img_type='exif_8',
            image="exif-orientation-examples/Landscape_8.jpg",
            ppoi="0.5x0.5",
            width=0,
            height=0
        )
        exif_8.image.create_on_demand = True
        exif_8_path = exif_8.image.thumbnail['100x100'].name
        # exif_8_img = exif_8.image.field.storage.open(exif_8_path)
        # exif_8_control = exif_8.image.field.storage.open(
        #     'verify-against/exif-orientation-examples/Landscape_8-thumbnail-100x100.jpg'
        # )
        # self.assertImageEqual(
        #     Image.open(exif_8_img),
        #     Image.open(exif_8_control)
        # )

    def test_horizontal_and_vertical_crop(self):
        """Test horizontal and vertical crops with 'extreme' PPOI values."""
        test_gif = VersatileImageTestModel.objects.get(img_type='gif')
        test_gif.image.create_on_demand = True
        test_gif.image.ppoi = (0, 0)
        # Vertical w/ PPOI == '0x0'
        vertical_image_crop = test_gif.image.field.storage.open(
            test_gif.image.crop['30x100'].name
        )
        vertical_image_crop_control = test_gif.image.field.storage.open(
            'verify-against/python-logo-crop-c0__0-30x100.gif'
        )
        self.assertImageEqual(
            Image.open(vertical_image_crop),
            Image.open(vertical_image_crop_control)
        )
        # Horizontal w/ PPOI == '0x0'
        horiz_image_crop = test_gif.image.field.storage.open(
            test_gif.image.crop['100x30'].name
        )
        horiz_image_crop_control = test_gif.image.field.storage.open(
            'verify-against/python-logo-crop-c0__0-100x30.gif'
        )
        self.assertImageEqual(
            Image.open(horiz_image_crop),
            Image.open(horiz_image_crop_control)
        )

        test_gif.image.ppoi = (1, 1)
        # Vertical w/ PPOI == '1x1'
        vertical_image_crop = test_gif.image.field.storage.open(
            test_gif.image.crop['30x100'].name
        )
        vertical_image_crop_control = test_gif.image.field.storage.open(
            'verify-against/python-logo-crop-c1__1-30x100.gif'
        )
        self.assertImageEqual(
            Image.open(vertical_image_crop),
            Image.open(vertical_image_crop_control)
        )
        # Horizontal w/ PPOI == '1x1'
        horiz_image_crop = test_gif.image.field.storage.open(
            test_gif.image.crop['100x30'].name
        )
        horiz_image_crop_control = test_gif.image.field.storage.open(
            'verify-against/python-logo-crop-c1__1-100x30.gif'
        )
        self.assertImageEqual(
            Image.open(horiz_image_crop),
            Image.open(horiz_image_crop_control)
        )

    def test_dummy_filter(self):
        """Test placeholder image functionality for filters."""
        self.png.optional_image.create_on_demand = True
        self.png.optional_image.filters.invert.url

    def test_crop_and_thumbnail_key_assignment(self):
        """Test placeholder image functionality for filters."""
        with self.assertRaises(NotImplementedError):
            jpg = VersatileImageTestModel.objects.get(img_type='jpg')
            jpg.image.crop['100x100'] = None

        with self.assertRaises(NotImplementedError):
            jpg = VersatileImageTestModel.objects.get(img_type='jpg')
            jpg.image.thumbnail['100x100'] = None

    def test_malformed_sized_image_key(self):
        """Test MalformedSizedImageKey exception."""
        with self.assertRaises(MalformedSizedImageKey):
            self.jpg.image.thumbnail['fooxbar']

    def test_registration_exceptions(self):
        """Ensure all registration-related exceptions fire as expected."""
        class A(object):
            pass

        with self.assertRaises(InvalidSizedImageSubclass):
            versatileimagefield_registry.register_sizer('a', A)

        with self.assertRaises(InvalidFilteredImageSubclass):
            versatileimagefield_registry.register_filter('a', A)

        with self.assertRaises(UnallowedSizerName):
            versatileimagefield_registry.register_sizer('chunks', CroppedImage)

        with self.assertRaises(UnallowedFilterName):
            versatileimagefield_registry.register_filter('_poop', InvertImage)

        with self.assertRaises(AlreadyRegistered):
            versatileimagefield_registry.register_sizer('crop', CroppedImage)

        with self.assertRaises(AlreadyRegistered):
            versatileimagefield_registry.register_filter('invert', InvertImage)

        with self.assertRaises(NotRegistered):
            versatileimagefield_registry.unregister_sizer('poop')

        with self.assertRaises(NotRegistered):
            versatileimagefield_registry.unregister_filter('poop')

    def test_unregister_methods(self):
        """Ensure versatileimagefield_registry unregister methods work."""
        self.assertIn('crop', versatileimagefield_registry._sizedimage_registry)
        versatileimagefield_registry.unregister_sizer('crop')
        self.assertNotIn('crop', versatileimagefield_registry._sizedimage_registry)
        versatileimagefield_registry.register_sizer('crop', CroppedImage)

        self.assertIn('invert', versatileimagefield_registry._filter_registry)
        versatileimagefield_registry.unregister_filter('invert')
        self.assertNotIn('invert', versatileimagefield_registry._filter_registry)
        versatileimagefield_registry.register_filter('invert', InvertImage)

    def test_save_form_data(self):
        """Test VersatileImageField.save_form_data."""
        with open(
            os.path.join(
                os.path.dirname(upath(__file__)),
                "test.png"
            ),
            'rb'
        ) as fp:
            image_data = fp.read()
        with open(
            os.path.join(
                os.path.dirname(upath(__file__)),
                "test2.png"
            ),
            'rb'
        ) as fp:
            image_data2 = fp.read()

        # Testing new uploads
        form = VersatileImageTestModelForm(
            data={'img_type': 'xxx'},
            files={
                'image_0': SimpleUploadedFile('test.png', image_data),
                'optional_image_0': SimpleUploadedFile('test2.png', image_data2)
            }
        )
        self.assertEqual(form.is_valid(), True)
        self.assertEqual(type(form.cleaned_data['image'][0]), SimpleUploadedFile)
        self.assertEqual(type(form.cleaned_data['optional_image'][0]), SimpleUploadedFile)
        instance = form.save(commit=False)
        self.assertEqual(instance.image.name.lstrip('./'), 'test.png')
        self.assertEqual(instance.optional_image.name.lstrip('./'), 'test2.png')

        # Testing updating files / PPOI values
        # Deleting optional_image file (since it'll be cleared with the next form)
        instance.optional_image.delete()
        form = VersatileImageTestModelForm(
            data={
                'img_type': 'xxx',
                'image_0': '',
                'image_1': '0.25x0.25',
                'optional_image-clear': 'on'
            },
            instance=instance
        )
        instance = form.save(commit=False)
        self.assertEqual(instance.image.ppoi, (0.25, 0.25))
        self.assertEqual(instance.optional_image.name, '')
        instance.image.delete(save=False)

    def test_processed_image_subclass_exceptions(self):
        """Ensure ProcessedImage subclasses throw NotImplementedError."""
        with self.assertRaises(NotImplementedError):
            class SizedImageSubclass(SizedImage):
                pass

            SizedImageSubclass('', '', False)

        with self.assertRaises(NotImplementedError):
            class SizedImageSubclass(SizedImage):
                filename_key = 'test'

            instance = SizedImageSubclass('', '', False)
            instance.process_image(image=None, image_format='JPEG', save_kwargs={}, width=100, height=100)

        with self.assertRaises(NotImplementedError):
            class FilteredImageSubclass(FilteredImage):
                filename_key = 'test'

            instance = FilteredImageSubclass(
                self.jpg.image.name,
                self.jpg.image.field.storage,
                False,
                filename_key='foo'
            )
            instance.process_image(image=None, image_format='JPEG', save_kwargs={})

    @override_settings(INSTALLED_APPS=('tests.test_autodiscover',))
    def test_autodiscover(self):
        """Test autodiscover ImportError."""
        self.assertRaises(ImportError, autodiscover)

    @override_settings(VERSATILEIMAGEFIELD_USE_PLACEHOLDIT=True)
    def test_placeholdit(self):
        """Test placehold.it integration."""
        jpg = VersatileImageTestModel.objects.get(img_type='jpg')
        self.assertEqual(
            jpg.optional_image_3.filters.invert.crop['400x400'].url,
            'http://placehold.it/400x400'
        )

    def test_template_rendering(self):
        """Test template rendering of image."""
        template = get_template("test-template.html")
        rendered = template.render({'instance': self.jpg})

        self.assertHTMLEqual(
            rendered,
            """
            <html>
              <body>
                <img id="image-crop" src="/media/__sized__/python-logo-crop-c0-25__0-25-400x400-70.jpg" />
                <img id="image-thumbnail" src="/media/__sized__/python-logo-thumbnail-400x400-70.jpg" />
                <img id="image-invert" src="/media/__filtered__/python-logo__invert__.jpg" />
                <img id="image-invert-crop"
                     src="/media/__sized__/__filtered__/python-logo__invert__-crop-c0-25__0-25-400x400-70.jpg" />
                <img id="optional-image-crop"
                     src="/media/__sized__/__placeholder__/placeholder-crop-c0-5__0-5-400x400.png" />
              </body>
            </html>
            """
        )

    def test_field_serialization(self):
        """Ensure VersatileImageField and PPOIField serialize correctly."""
        output = serializers.serialize(
            'json',
            VersatileImageTestModel.objects.filter(img_type='png')
        )
        self.assertJSONEqual(
            output,
            [
                {
                    "fields": {
                        "img_type": "png",
                        "ppoi": "0.5x0.5",
                        "width": 601,
                        "height": 203,
                        "image": "python-logo.png",
                        "optional_image_3": "",
                        "optional_image_2": "",
                        "optional_image": "python-logo.jpg"
                    },
                    "model": "tests.versatileimagetestmodel",
                    "pk": self.png.pk
                }
            ]
        )

    def test_bound_form_data(self):
        """Ensure correct data displays after form validation errors."""
        response = self.client.post(
            self.admin_url,
            {'required_text_field': ''},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            """
            <img src="/media/__sized__/python-logo-thumbnail-300x300.png"
                 id="image_0_imagepreview" data-hidden_field_id="id_image_1"
                 data-point_stage_id="image_0_point-stage"
                 data-ppoi_id="image_0_ppoi" class="sizedimage-preview" />
            """,
            html=True
        )

    def test_individual_rendition_cache_clear(self):
        """Test that VersatileImageField can clear individual cache entries."""
        expected_image_url = '/media/__sized__/delete-test/python-logo-delete-test-thumbnail-100x100-70.jpg'
        self.assertEqual(cache.get(expected_image_url), None)
        img = self.delete_test
        img.image.create_on_demand = True
        img_url = img.image.thumbnail['100x100'].url
        del img_url
        self.assertEqual(cache.get(expected_image_url), 1)
        img.image.thumbnail['100x100'].delete()
        self.assertEqual(cache.get(expected_image_url), None)
        self.assertFalse(
            img.image.field.storage.exists(
                '__sized__/delete-test/python-logo-delete-test-thumbnail-100x100-70.jpg'
            )
        )

    def test_rendition_delete(self):
        """Test rendition deletion."""
        img = self.delete_test
        self.assertFalse(
            img.image.field.storage.exists(
                '__sized__/delete-test/python-logo-delete-test-thumbnail-100x100-70.jpg'
            )
        )
        img.image.create_on_demand = True

        thumb_url = img.image.thumbnail['100x100'].url
        self.assertEqual(cache.get(thumb_url), 1)
        self.assertTrue(
            img.image.field.storage.exists(
                '__sized__/delete-test/python-logo-delete-test-thumbnail-100x100-70.jpg'
            )
        )
        img.image.delete_all_created_images()
        invert_url = img.image.filters.invert.url
        self.assertEqual(cache.get(invert_url), 1)
        self.assertTrue(
            img.image.field.storage.exists(
                'delete-test/__filtered__/python-logo-delete-test__invert__.jpg'
            )
        )

        invert_and_thumb_url = img.image.filters.invert.thumbnail['100x100'].url
        self.assertEqual(cache.get(invert_and_thumb_url), 1)
        self.assertTrue(
            img.image.field.storage.exists(
                '__sized__/delete-test/__filtered__/python-logo-delete-test__invert__-thumbnail-100x100-70.jpg'
            )
        )

        img.image.delete_all_created_images()
        self.assertEqual(cache.get(thumb_url), None)
        self.assertFalse(
            img.image.field.storage.exists(
                '__sized__/delete-test/python-logo-delete-test-thumbnail-100x100-70.jpg'
            )
        )

        self.assertEqual(cache.get(invert_url), None)
        self.assertFalse(
            img.image.field.storage.exists(
                'delete-test/__filtered__/python-logo-delete-test__invert__.jpg'
            )
        )

        self.assertEqual(cache.get(invert_and_thumb_url), None)
        self.assertFalse(
            img.image.field.storage.exists(
                '__sized__/delete-test/__filtered__/python-logo-delete-test__invert__-thumbnail-100x100-70.jpg'
            )
        )

    def test_filtered_filename(self):
        """Test building a filtered filename from the original name."""
        self.assertEqual(
            get_filtered_filename('test.png', 'inverted'),
            'test__inverted__.png'
        )
        self.assertEqual(
            get_filtered_filename('test', 'inverted'),
            'test__inverted__.jpg'
        )

    def test_resized_filename(self):
        """Test building a filename for a resized image."""
        self.assertEqual(
            get_resized_filename('test.png', 100, 100, 'thumbnail'),
            'test-thumbnail-100x100.png'
        )
        self.assertEqual(
            get_resized_filename('test', 100, 100, 'thumbnail'),
            'test-thumbnail-100x100-{}.jpg'.format(QUAL)
        )

    def test_transparent_gif_preprocess(self):
        """Test preprocessing a transparent gif image."""
        instance = VersatileImageTestModel.objects.create(
            img_type='tgif',
            image='transparent.gif',
            ppoi='1x1',
            width=0,
            height=0
        )
        processor = ProcessedImage(instance.image.name, instance.image.field.storage, True)
        image_info = processor.retrieve_image(instance.image.name)
        image, save_kwargs = processor.preprocess_GIF(image_info[0])
        self.assertEqual(save_kwargs['transparency'], image.info['transparency'])

    def test_cmyk_jpg_preprocess(self):
        """Test preprocessing a CMYK image converts it to RGB."""
        instance = VersatileImageTestModel.objects.create(
            img_type='cmyk',
            image='cmyk.jpg',
            ppoi='0.5x0.5',
            width=0,
            height=0
        )
        processor = ProcessedImage(instance.image.name, instance.image.field.storage, True)
        image_info = processor.retrieve_image(instance.image.name)
        image, save_kwargs = processor.preprocess_JPEG(image_info[0])

        self.assertEqual(image.mode, 'RGB')

    def test_corrupt_file(self):
        with open(
            os.path.join(
                os.path.dirname(upath(__file__)),
                "test.png"
            ),
            'rb'
        ) as fp:
            # Anything which cannot be resized or thumbnailed, but checks out
            # when only looking at basic header data
            content = fp.read()[:100]

        instance = VersatileImageTestModel()
        instance.image.save(
            'stuff.png',
            ContentFile(content),
            save=True,
        )

        instance.image.create_on_demand = True
        with self.assertRaises((AttributeError, IOError, OSError)):
            instance.image.thumbnail['200x200']

        admin_url = reverse('admin:tests_versatileimagetestmodel_change', args=(instance.pk,))
        response = self.client.get(admin_url)
        response.render()
        self.assertContains(
            response,
            '<label class="versatileimagefield-label">Currently</label>',
        )
        self.assertContains(
            response,
            '<a href="/media/stuff',
        )

        instance.image.delete(save=False)
