from .....product.models import Product
from ....context import SaleorContext
from ...dataloaders import ProductByIdLoader, ProductTypeByProductIdLoader


def test_returns_product_type_of_already_loaded_product_after_type_change(
    product, product_type_without_variant
):
    # Regression test for SALEOR-CORE-8ED: a product whose type changed after it was
    # loaded raised KeyError, as its old product_type_id was missing from the lookup.
    # given
    old_product_type = product.product_type
    assert old_product_type.pk != product_type_without_variant.pk
    context = SaleorContext()
    ProductByIdLoader(context).load(product.pk).get()
    Product.objects.filter(pk=product.pk).update(
        product_type=product_type_without_variant
    )

    # when
    product_types = ProductTypeByProductIdLoader(context).load_many([product.pk]).get()

    # then
    # The old type is expected: dataloaders are a per-request snapshot, so the product
    # type must match the product already loaded in this request, not a newer DB state.
    assert product_types == [old_product_type]
