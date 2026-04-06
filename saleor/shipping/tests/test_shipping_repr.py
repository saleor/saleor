def test_shipping_method_data_repr(shipping_method_data):
    shipping_repr = repr(shipping_method_data)

    assert f"id={shipping_method_data.id}" in shipping_repr
    assert f"is_external={shipping_method_data.is_external}" in shipping_repr
    assert f"type={shipping_method_data.type}" in shipping_repr
    assert f"price={shipping_method_data.price}" in shipping_repr
