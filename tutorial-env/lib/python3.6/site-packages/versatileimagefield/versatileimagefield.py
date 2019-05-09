"""Default sizer & filter definitions."""
from __future__ import division
from __future__ import unicode_literals

from django.utils.six import BytesIO

from PIL import Image, ImageOps

from .datastructures import FilteredImage, SizedImage
from .registry import versatileimagefield_registry


class CroppedImage(SizedImage):
    """
    A SizedImage subclass that creates a 'cropped' image.

    See the `process_image` method for more details.
    """

    filename_key = 'crop'
    filename_key_regex = r'crop-c[0-9-]+__[0-9-]+'

    def get_filename_key(self):
        """Return the filename key for cropped images."""
        return "{key}-c{ppoi}".format(
            key=self.filename_key,
            ppoi=self.ppoi_as_str()
        )

    def crop_on_centerpoint(self, image, width, height, ppoi=(0.5, 0.5)):
        """
        Return a PIL Image instance cropped from `image`.

        Image has an aspect ratio provided by dividing `width` / `height`),
        sized down to `width`x`height`. Any 'excess pixels' are trimmed away
        in respect to the pixel of `image` that corresponds to `ppoi` (Primary
        Point of Interest).

        `image`: A PIL Image instance
        `width`: Integer, width of the image to return (in pixels)
        `height`: Integer, height of the image to return (in pixels)
        `ppoi`: A 2-tuple of floats with values greater than 0 and less than 1
                These values are converted into a cartesian coordinate that
                signifies the 'center pixel' which the crop will center on
                (to trim the excess from the 'long side').

        Determines whether to trim away pixels from either the left/right or
        top/bottom sides by comparing the aspect ratio of `image` vs the
        aspect ratio of `width`x`height`.

        Will trim from the left/right sides if the aspect ratio of `image`
        is greater-than-or-equal-to the aspect ratio of `width`x`height`.

        Will trim from the top/bottom sides if the aspect ration of `image`
        is less-than the aspect ratio or `width`x`height`.

        Similar to Kevin Cazabon's ImageOps.fit method but uses the
        ppoi value as an absolute centerpoint (as opposed as a
        percentage to trim off the 'long sides').
        """
        ppoi_x_axis = int(image.size[0] * ppoi[0])
        ppoi_y_axis = int(image.size[1] * ppoi[1])
        center_pixel_coord = (ppoi_x_axis, ppoi_y_axis)
        # Calculate the aspect ratio of `image`
        orig_aspect_ratio = float(
            image.size[0]
        ) / float(
            image.size[1]
        )
        crop_aspect_ratio = float(width) / float(height)

        # Figure out if we're trimming from the left/right or top/bottom
        if orig_aspect_ratio >= crop_aspect_ratio:
            # `image` is wider than what's needed,
            # crop from left/right sides
            orig_crop_width = int(
                (crop_aspect_ratio * float(image.size[1])) + 0.5
            )
            orig_crop_height = image.size[1]
            crop_boundary_top = 0
            crop_boundary_bottom = orig_crop_height
            crop_boundary_left = center_pixel_coord[0] - (orig_crop_width // 2)
            crop_boundary_right = crop_boundary_left + orig_crop_width
            if crop_boundary_left < 0:
                crop_boundary_left = 0
                crop_boundary_right = crop_boundary_left + orig_crop_width
            elif crop_boundary_right > image.size[0]:
                crop_boundary_right = image.size[0]
                crop_boundary_left = image.size[0] - orig_crop_width

        else:
            # `image` is taller than what's needed,
            # crop from top/bottom sides
            orig_crop_width = image.size[0]
            orig_crop_height = int(
                (float(image.size[0]) / crop_aspect_ratio) + 0.5
            )
            crop_boundary_left = 0
            crop_boundary_right = orig_crop_width
            crop_boundary_top = center_pixel_coord[1] - (orig_crop_height // 2)
            crop_boundary_bottom = crop_boundary_top + orig_crop_height
            if crop_boundary_top < 0:
                crop_boundary_top = 0
                crop_boundary_bottom = crop_boundary_top + orig_crop_height
            elif crop_boundary_bottom > image.size[1]:
                crop_boundary_bottom = image.size[1]
                crop_boundary_top = image.size[1] - orig_crop_height
        # Cropping the image from the original image
        cropped_image = image.crop(
            (
                crop_boundary_left,
                crop_boundary_top,
                crop_boundary_right,
                crop_boundary_bottom
            )
        )
        # Resizing the newly cropped image to the size specified
        # (as determined by `width`x`height`)
        return cropped_image.resize(
            (width, height),
            Image.ANTIALIAS
        )

    def process_image(self, image, image_format, save_kwargs,
                      width, height):
        """
        Return a BytesIO instance of `image` cropped to `width` and `height`.

        Cropping will first reduce an image down to its longest side
        and then crop inwards centered on the Primary Point of Interest
        (as specified by `self.ppoi`)
        """
        imagefile = BytesIO()
        palette = image.getpalette()
        cropped_image = self.crop_on_centerpoint(
            image,
            width,
            height,
            self.ppoi
        )

        # Using ImageOps.fit on GIFs can introduce issues with their palette
        # Solution derived from: http://stackoverflow.com/a/4905209/1149774
        if image_format == 'GIF':
            cropped_image.putpalette(palette)

        cropped_image.save(
            imagefile,
            **save_kwargs
        )

        return imagefile


class ThumbnailImage(SizedImage):
    """
    Sizes an image down to fit within a bounding box.

    See the `process_image()` method for more information
    """

    filename_key = 'thumbnail'

    def process_image(self, image, image_format, save_kwargs,
                      width, height):
        """
        Return a BytesIO instance of `image` that fits in a bounding box.

        Bounding box dimensions are `width`x`height`.
        """
        imagefile = BytesIO()
        image.thumbnail(
            (width, height),
            Image.ANTIALIAS
        )
        image.save(
            imagefile,
            **save_kwargs
        )
        return imagefile


class InvertImage(FilteredImage):
    """
    Invert the color palette of an image.

    See the `process_image()` for more specifics
    """

    def process_image(self, image, image_format, save_kwargs={}):
        """Return a BytesIO instance of `image` with inverted colors."""
        imagefile = BytesIO()
        inv_image = ImageOps.invert(image)
        inv_image.save(
            imagefile,
            **save_kwargs
        )
        return imagefile


versatileimagefield_registry.register_sizer('crop', CroppedImage)
versatileimagefield_registry.register_sizer('thumbnail', ThumbnailImage)
versatileimagefield_registry.register_filter('invert', InvertImage)
