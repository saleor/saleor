from ..products.utils import create_digital_product_type


def test_process_checkout_with_digital_product(
    staff_api_client, permission_manage_product_types_and_attributes
):
    product_type_id = create_digital_product_type(
        staff_api_client, [permission_manage_product_types_and_attributes]
    )
    assert product_type_id is not None
