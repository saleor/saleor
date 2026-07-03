from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def create_image(image_name="product2"):
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1), color=(255, 0, 0, 0))
    image.save(img_data, format="JPEG")
    image = SimpleUploadedFile(image_name + ".jpg", img_data.getvalue(), "image/jpeg")
    return image, image_name


def create_image_without_extension(image_name="product_img_without_extension"):
    # Ensure the image_name does not have an extension
    image_name = image_name.split(".")[0]
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    img = SimpleUploadedFile(image_name, img_data.getvalue(), "image/jpeg")
    return img, image_name


def create_zip_file_with_image_ext():
    file_name = "product.jpg"
    file_data = SimpleUploadedFile(file_name, b"product_data", "application/zip")
    return file_data, file_name
