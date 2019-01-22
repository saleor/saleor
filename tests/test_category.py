from saleor.product.filters import ProductCategoryFilter


def test_product_category_filter_filters_from_child_category(
        product_type, categories_tree):
    product_filter = ProductCategoryFilter(data={}, category=categories_tree)
    merged_attributes = (
        product_filter._get_merged_attributes().get_attributes())

    attribute = product_type.product_attributes.get()
    variant = product_type.variant_attributes.get()

    assert attribute.slug in merged_attributes
    assert variant.slug in merged_attributes
