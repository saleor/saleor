from saleor.webhook.payload_serializers import PythonSerializer


def test_python_serializer_extra_model_fields(product_with_single_variant):
    serializer = PythonSerializer(
        extra_model_fields={"ProductVariant": ("quantity", "quantity_allocated")}
    )
    annotated_variant = (
        product_with_single_variant.variants.annotate_quantities().first()
    )
    serializer._current = {"test_item": "test_value"}
    result = serializer.get_dump_object(annotated_variant)
    assert result["type"] == "ProductVariant"
    assert result["test_item"] == "test_value"
    assert result["quantity"] == str(annotated_variant.quantity)
    assert result["quantity_allocated"] == str(annotated_variant.quantity_allocated)


def test_python_serializer_extra_model_fields_incorrect_fields(
    product_with_single_variant,
):
    serializer = PythonSerializer(
        extra_model_fields={
            "NonExistingModel": ("__dummy",),
            "ProductVariant": ("__not_on_model",),
        }
    )
    annotated_variant = (
        product_with_single_variant.variants.annotate_quantities().first()
    )
    serializer._current = {"test_item": "test_value"}
    result = serializer.get_dump_object(annotated_variant)
    assert result["type"] == "ProductVariant"
    assert result["test_item"] == "test_value"
