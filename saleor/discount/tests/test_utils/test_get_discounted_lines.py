import pytest

from ....checkout.fetch import fetch_checkout_lines
from ...interface import VoucherCatalogue, VoucherInfo, fetch_voucher_info
from ...utils.voucher import get_discounted_lines


@pytest.fixture
def checkout_lines_with_distinct_first_product(
    checkout_with_items, category_list, product_type_list, collection
):
    """Checkout lines where only the first line's product has its own catalogue."""
    lines, _ = fetch_checkout_lines(checkout_with_items, skip_recalculation=True)
    product = lines[0].product
    product.category = category_list[0]
    product.product_type = product_type_list[0]
    product.save(update_fields=["category", "product_type"])
    collection.products.add(product)
    lines, _ = fetch_checkout_lines(checkout_with_items, skip_recalculation=True)
    assert len(lines) == 4
    return lines


@pytest.mark.parametrize(
    ("_case", "catalogue_field", "get_pk"),
    [
        ("product", "product_pks", lambda line: line.product.pk),
        ("variant", "variant_pks", lambda line: line.variant.pk),
        ("collection", "collection_pks", lambda line: line.collections[0].pk),
        ("category", "category_pks", lambda line: line.product.category_id),
        ("product_type", "product_type_pks", lambda line: line.product.product_type_id),
    ],
)
def test_exclusion_without_includes_skips_only_excluded_line(
    _case,
    catalogue_field,
    get_pk,
    checkout_lines_with_distinct_first_product,
    voucher,
):
    # given
    lines = checkout_lines_with_distinct_first_product
    excluded_line = lines[0]
    voucher_info = VoucherInfo(
        voucher=voucher,
        voucher_code=None,
        included=VoucherCatalogue(),
        excluded=VoucherCatalogue(
            **{catalogue_field: frozenset({get_pk(excluded_line)})}
        ),
    )

    # when
    discounted_lines = get_discounted_lines(lines, voucher_info)

    # then
    assert discounted_lines == lines[1:]


def test_exclusion_wins_over_include_of_other_dimension(
    checkout_lines_with_distinct_first_product, voucher, category
):
    # given
    lines = checkout_lines_with_distinct_first_product
    excluded_product = lines[1].product
    assert {line.product.category_id for line in lines[1:]} == {category.pk}
    voucher_info = VoucherInfo(
        voucher=voucher,
        voucher_code=None,
        included=VoucherCatalogue(category_pks=frozenset({category.pk})),
        excluded=VoucherCatalogue(product_pks=frozenset({excluded_product.pk})),
    )

    # when
    discounted_lines = get_discounted_lines(lines, voucher_info)

    # then
    assert discounted_lines == lines[2:]


def test_product_type_include_matches_alongside_category_include(
    checkout_lines_with_distinct_first_product, voucher, category_list
):
    # given
    lines = checkout_lines_with_distinct_first_product
    second_line_product = lines[1].product
    second_line_product.category = category_list[1]
    second_line_product.save(update_fields=["category"])
    voucher_info = VoucherInfo(
        voucher=voucher,
        voucher_code=None,
        included=VoucherCatalogue(
            product_type_pks=frozenset({lines[0].product.product_type_id}),
            category_pks=frozenset({category_list[1].pk}),
        ),
        excluded=VoucherCatalogue(),
    )

    # when
    discounted_lines = get_discounted_lines(lines, voucher_info)

    # then
    assert discounted_lines == lines[:2]


def test_gift_line_is_skipped_when_voucher_has_exclusions(
    checkout_lines_with_distinct_first_product, voucher
):
    # given
    lines = checkout_lines_with_distinct_first_product
    gift_line = lines[1].line
    gift_line.is_gift = True
    gift_line.save(update_fields=["is_gift"])
    voucher_info = VoucherInfo(
        voucher=voucher,
        voucher_code=None,
        included=VoucherCatalogue(),
        excluded=VoucherCatalogue(product_pks=frozenset({lines[0].product.pk})),
    )

    # when
    discounted_lines = get_discounted_lines(lines, voucher_info)

    # then
    assert discounted_lines == lines[2:]


def test_fetch_voucher_info_reads_every_catalogue_relation(
    voucher,
    product_list,
    product_variant_list,
    collection_list,
    category_list,
    product_type_list,
):
    # given
    voucher.products.add(product_list[0])
    voucher.variants.add(product_variant_list[0])
    voucher.collections.add(collection_list[0])
    voucher.categories.add(category_list[0])
    voucher.product_types.add(product_type_list[0])
    voucher.excluded_products.add(product_list[1])
    voucher.excluded_variants.add(product_variant_list[1])
    voucher.excluded_collections.add(collection_list[1])
    voucher.excluded_categories.add(category_list[1])
    voucher.excluded_product_types.add(product_type_list[1])
    voucher_code = voucher.codes.get().code

    # when
    voucher_info = fetch_voucher_info(voucher, voucher_code)

    # then
    assert voucher_info.voucher_code == voucher_code
    assert voucher_info.included == VoucherCatalogue(
        product_pks=frozenset({product_list[0].pk}),
        variant_pks=frozenset({product_variant_list[0].pk}),
        collection_pks=frozenset({collection_list[0].pk}),
        category_pks=frozenset({category_list[0].pk}),
        product_type_pks=frozenset({product_type_list[0].pk}),
    )
    assert voucher_info.excluded == VoucherCatalogue(
        product_pks=frozenset({product_list[1].pk}),
        variant_pks=frozenset({product_variant_list[1].pk}),
        collection_pks=frozenset({collection_list[1].pk}),
        category_pks=frozenset({category_list[1].pk}),
        product_type_pks=frozenset({product_type_list[1].pk}),
    )
