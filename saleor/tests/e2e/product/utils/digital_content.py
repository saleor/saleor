from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from ...utils import get_graphql_content, get_multipart_request_body

DIGITAL_CONTENT_CREATE_MUTATION = """
mutation createDigitalContent($variantId: ID!, $input: DigitalContentUploadInput!) {
  digitalContentCreate(input: $input, variantId: $variantId) {
    errors {
      field
      message
      code
    }
    variant {
      id
    }
    content {
      id
      contentFile
    }
  }
}
"""


def create_image(image_name):
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1), color=(255, 0, 0, 0))
    image.save(img_data, format="JPEG")
    image = SimpleUploadedFile(image_name + ".jpg", img_data.getvalue(), "image/jpeg")
    return image, image_name


def create_digital_content(staff_api_client, product_variant_id):
    image_file, image_name = create_image("sample_image_as_digital_content")
    variables = {
        "input": {
            "useDefaultSettings": True,
            "automaticFulfillment": True,
            "contentFile": image_name,
        },
        "variantId": product_variant_id,
    }

    request_body = get_multipart_request_body(
        DIGITAL_CONTENT_CREATE_MUTATION, variables, image_file, image_name
    )
    response = staff_api_client.post_multipart(request_body)
    content = get_graphql_content(response)

    assert content["data"]["digitalContentCreate"]["errors"] == []

    variant_data = content["data"]["digitalContentCreate"]["variant"]
    assert variant_data["id"] == product_variant_id
    digital_content_data = content["data"]["digitalContentCreate"]["content"]
    assert digital_content_data["id"] is not None
    assert image_name in digital_content_data["contentFile"]

    return digital_content_data
