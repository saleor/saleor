from saleor.product.filters import ProductCategoryFilter


def test_product_category_filter_filters_from_child_category(
    product_type, categories_tree
):
    product_filter = ProductCategoryFilter(data={}, category=categories_tree)
    attributes = product_filter._get_attributes()

    product_attr = product_type.product_attributes.get()
    variant_attr = product_type.variant_attributes.get()

    assert product_attr in attributes
    assert variant_attr in attributes
