from datetime import datetime
from unittest.mock import patch

from .....attribute.models import (
    Attribute,
    AttributeValue,
)
from .....attribute.tests.model_helpers import get_product_attributes
from .....attribute.utils import associate_attribute_values_to_instance
from .....product.models import Product, ProductMedia, ProductVariant, VariantMedia
from .....tests.utils import dummy_editorjs
from .....warehouse.models import Warehouse
from ....utils import ProductExportFields
from ....utils.products_data import (
    AttributeData,
    add_attribute_info_to_data,
    add_channel_info_to_data,
    add_collection_info_to_data,
    add_image_uris_to_data,
    add_warehouse_info_to_data,
    get_products_relations_data,
    get_variants_relations_data,
    prepare_products_relations_data,
    prepare_variants_relations_data,
)
from .utils import (
    add_channel_to_expected_product_data,
    add_channel_to_expected_variant_data,
    add_product_attribute_data_to_expected_data,
    add_stocks_to_expected_data,
    add_variant_attribute_data_to_expected_data,
)


@patch("saleor.csv.utils.products_data.prepare_products_relations_data")
def test_get_products_relations_data(prepare_products_data_mocked, product_list):
    # given
    qs = Product.objects.all()
    export_fields = {
        "collections__slug",
        "media__image",
        "name",
        "description",
    }
    attribute_ids = []
    channel_ids = []

    # when
    get_products_relations_data(qs, export_fields, attribute_ids, channel_ids)

    # then
    assert prepare_products_data_mocked.call_count == 1
    args, kwargs = prepare_products_data_mocked.call_args
    assert set(args[0].values_list("pk", flat=True)) == set(
        qs.values_list("pk", flat=True)
    )
    assert args[1:] == (
        {"collections__slug", "media__image"},
        attribute_ids,
        channel_ids,
    )


@patch("saleor.csv.utils.products_data.prepare_products_relations_data")
def test_get_products_relations_data_no_relations_fields(
    prepare_products_data_mocked, product_list
):
    # given
    qs = Product.objects.all()
    export_fields = {"name", "description"}
    attribute_ids = []
    channel_ids = []

    # when
    get_products_relations_data(qs, export_fields, attribute_ids, channel_ids)

    # then
    prepare_products_data_mocked.assert_not_called()


@patch("saleor.csv.utils.products_data.prepare_products_relations_data")
def test_get_products_relations_data_attribute_ids(
    prepare_products_data_mocked,
    product_list,
    file_attribute,
    product_type_page_reference_attribute,
    product_type_product_reference_attribute,
    page,
):
    # given
    product = product_list[0]
    product.product_type.product_attributes.add(
        file_attribute,
        product_type_page_reference_attribute,
        product_type_product_reference_attribute,
    )
    associate_attribute_values_to_instance(
        product,
        {file_attribute.id: [file_attribute.values.first()]},
    )
    page_ref_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        slug=f"{product.pk}_{page.pk}",
        name=page.title,
    )
    associate_attribute_values_to_instance(
        product,
        {product_type_page_reference_attribute.id: [page_ref_value]},
    )
    product_ref_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        slug=f"{product.pk}_{product_list[1].pk}",
        name=product_list[1].name,
    )
    associate_attribute_values_to_instance(
        product,
        {product_type_product_reference_attribute.id: [product_ref_value]},
    )

    qs = Product.objects.all()
    export_fields = {"name", "description"}
    attribute_ids = list(Attribute.objects.values_list("pk", flat=True))
    channel_ids = []

    # when
    get_products_relations_data(qs, export_fields, attribute_ids, channel_ids)

    # then
    assert prepare_products_data_mocked.call_count == 1
    args, kwargs = prepare_products_data_mocked.call_args
    assert set(args[0].values_list("pk", flat=True)) == set(
        qs.values_list("pk", flat=True)
    )
    assert args[1:] == (set(), attribute_ids, channel_ids)


@patch("saleor.csv.utils.products_data.prepare_products_relations_data")
def test_get_products_relations_data_channel_ids(
    prepare_products_data_mocked, product_list, channel_USD, channel_PLN
):
    # given
    qs = Product.objects.all()
    export_fields = {"name", "description"}
    attribute_ids = []
    channel_ids = [channel_PLN.pk, channel_USD.pk]

    # when
    get_products_relations_data(qs, export_fields, attribute_ids, channel_ids)

    # then
    assert prepare_products_data_mocked.call_count == 1
    args, kwargs = prepare_products_data_mocked.call_args
    assert set(args[0].values_list("pk", flat=True)) == set(
        qs.values_list("pk", flat=True)
    )
    assert args[1:] == (set(), attribute_ids, channel_ids)


def test_prepare_products_relations_data(
    product_with_image,
    collection_list,
    channel_USD,
    channel_PLN,
    file_attribute,
    product_type_page_reference_attribute,
    page,
):
    # given
    pk = product_with_image.pk

    product_with_image.product_type.product_attributes.add(
        file_attribute, product_type_page_reference_attribute
    )
    associate_attribute_values_to_instance(
        product_with_image,
        {file_attribute.id: [file_attribute.values.first()]},
    )
    ref_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        reference_page=page,
        slug=f"{product_with_image.pk}_{page.pk}",
        name=page.title,
        date_time=None,
    )
    associate_attribute_values_to_instance(
        product_with_image,
        {product_type_page_reference_attribute.id: [ref_value]},
    )

    collection_list[0].products.add(product_with_image)
    collection_list[1].products.add(product_with_image)

    qs = Product.objects.all()
    fields = set(
        ProductExportFields.HEADERS_TO_FIELDS_MAPPING["product_many_to_many"].values()
    )
    attribute_ids = [
        str(attr.pk) for attr in get_product_attributes(product_with_image)
    ]
    channel_ids = [str(channel_PLN.pk), str(channel_USD.pk)]

    # when
    result = prepare_products_relations_data(qs, fields, attribute_ids, channel_ids)

    # then
    collections = ", ".join(
        sorted([collection.slug for collection in collection_list[:2]])
    )
    images = ", ".join(
        [
            "http://mirumee.com/media/" + image.image.name
            for image in product_with_image.media.all()
        ]
    )
    expected_result = {pk: {"collections__slug": collections, "media__image": images}}

    expected_result = add_product_attribute_data_to_expected_data(
        expected_result, product_with_image, attribute_ids, pk
    )

    expected_result = add_channel_to_expected_product_data(
        expected_result, product_with_image, channel_ids, pk
    )

    assert result == expected_result


def test_prepare_products_relations_data_only_fields(
    product_with_image, collection_list
):
    # given
    pk = product_with_image.pk
    collection_list[0].products.add(product_with_image)
    collection_list[1].products.add(product_with_image)
    qs = Product.objects.all()
    fields = {"collections__slug"}
    attribute_ids = []
    channel_ids = []

    # when
    result = prepare_products_relations_data(qs, fields, attribute_ids, channel_ids)

    # then
    collections = ", ".join(
        sorted([collection.slug for collection in collection_list[:2]])
    )
    expected_result = {pk: {"collections__slug": collections}}

    assert result == expected_result


def test_prepare_products_relations_data_only_attributes_ids(
    product_with_image, collection_list
):
    # given
    pk = product_with_image.pk
    collection_list[0].products.add(product_with_image)
    collection_list[1].products.add(product_with_image)
    qs = Product.objects.all()
    fields = {"name"}
    attribute_ids = [
        str(attr.pk) for attr in get_product_attributes(product_with_image)
    ]
    channel_ids = []

    # when
    result = prepare_products_relations_data(qs, fields, attribute_ids, channel_ids)

    # then
    expected_result = {pk: {}}

    expected_result = add_product_attribute_data_to_expected_data(
        expected_result, product_with_image, attribute_ids, pk
    )

    assert result == expected_result


def test_prepare_products_relations_data_only_channel_ids(
    product_with_image, collection_list, channel_PLN, channel_USD
):
    # given
    pk = product_with_image.pk
    collection_list[0].products.add(product_with_image)
    collection_list[1].products.add(product_with_image)
    qs = Product.objects.all()
    fields = {"name"}
    attribute_ids = []
    channel_ids = [str(channel_PLN.pk), str(channel_USD.pk)]

    # when
    result = prepare_products_relations_data(qs, fields, attribute_ids, channel_ids)

    # then
    expected_result = {pk: {}}

    expected_result = add_channel_to_expected_product_data(
        expected_result, product_with_image, channel_ids, pk
    )

    assert result == expected_result


@patch("saleor.csv.utils.products_data.prepare_variants_relations_data")
def test_get_variants_relations_data(prepare_variants_data_mocked, product_list):
    # given
    qs = Product.objects.all()
    export_fields = {
        "collections__slug",
        "variants__sku",
        "variants__media__image",
    }
    attribute_ids = []
    warehouse_ids = []
    channel_ids = []

    # when
    get_variants_relations_data(
        qs, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    assert prepare_variants_data_mocked.call_count == 1
    args, kwargs = prepare_variants_data_mocked.call_args
    assert set(args[0].values_list("pk", flat=True)) == set(
        qs.values_list("pk", flat=True)
    )
    assert args[1:] == (
        {"variants__media__image"},
        attribute_ids,
        warehouse_ids,
        channel_ids,
    )


@patch("saleor.csv.utils.products_data.prepare_variants_relations_data")
def test_get_variants_relations_data_no_relations_fields(
    prepare_variants_data_mocked, product_list
):
    # given
    qs = Product.objects.all()
    export_fields = {"name", "variants__sku"}
    attribute_ids = []
    warehouse_ids = []
    channel_ids = []

    # when
    get_variants_relations_data(
        qs, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    prepare_variants_data_mocked.assert_not_called()


@patch("saleor.csv.utils.products_data.prepare_variants_relations_data")
def test_get_variants_relations_data_attribute_ids(
    prepare_variants_data_mocked,
    product_list,
    file_attribute,
    product_type_page_reference_attribute,
    product_type_product_reference_attribute,
    page,
):
    # given
    product = product_list[0]
    product.product_type.variant_attributes.add(
        file_attribute,
        product_type_page_reference_attribute,
        product_type_product_reference_attribute,
    )
    variant = product.variants.first()
    associate_attribute_values_to_instance(
        variant,
        {file_attribute.id: [file_attribute.values.first()]},
    )
    # add page reference attribute
    page_ref_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        slug=f"{variant.pk}_{page.pk}",
        name=page.title,
    )
    associate_attribute_values_to_instance(
        variant,
        {product_type_page_reference_attribute.id: [page_ref_value]},
    )
    # add product reference attribute
    product_ref_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        slug=f"{variant.pk}_{product_list[1].pk}",
        name=product_list[1].name,
    )
    associate_attribute_values_to_instance(
        variant,
        {product_type_product_reference_attribute.id: [product_ref_value]},
    )

    qs = Product.objects.all()
    export_fields = {"name", "variants__sku"}
    attribute_ids = list(Attribute.objects.values_list("pk", flat=True))
    warehouse_ids = []
    channel_ids = []

    # when
    get_variants_relations_data(
        qs, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    assert prepare_variants_data_mocked.call_count == 1
    args, kwargs = prepare_variants_data_mocked.call_args
    assert set(args[0].values_list("pk", flat=True)) == set(
        qs.values_list("pk", flat=True)
    )
    assert args[1:] == (set(), attribute_ids, warehouse_ids, channel_ids)


@patch("saleor.csv.utils.products_data.prepare_variants_relations_data")
def test_get_variants_relations_data_warehouse_ids(
    prepare_variants_data_mocked, product_list, warehouses
):
    # given
    qs = Product.objects.all()
    export_fields = {"name", "variants__sku"}
    attribute_ids = []
    warehouse_ids = list(Warehouse.objects.values_list("pk", flat=True))
    channel_ids = []

    # when
    get_variants_relations_data(
        qs, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    assert prepare_variants_data_mocked.call_count == 1
    args, kwargs = prepare_variants_data_mocked.call_args
    assert set(args[0].values_list("pk", flat=True)) == set(
        qs.values_list("pk", flat=True)
    )
    assert args[1:] == (set(), attribute_ids, warehouse_ids, channel_ids)


@patch("saleor.csv.utils.products_data.prepare_variants_relations_data")
def test_get_variants_relations_data_channel_ids(
    prepare_variants_data_mocked, product_list, channel_USD, channel_PLN
):
    # given
    qs = Product.objects.all()
    export_fields = {"name", "variants__sku"}
    attribute_ids = []
    warehouse_ids = []
    channel_ids = [channel_PLN.pk, channel_USD.pk]

    # when
    get_variants_relations_data(
        qs, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    assert prepare_variants_data_mocked.call_count == 1
    args, kwargs = prepare_variants_data_mocked.call_args
    assert set(args[0].values_list("pk", flat=True)) == set(
        qs.values_list("pk", flat=True)
    )
    assert args[1:] == (set(), attribute_ids, warehouse_ids, channel_ids)


@patch("saleor.csv.utils.products_data.prepare_variants_relations_data")
def test_get_variants_relations_data_attributes_warehouses_and_channels_ids(
    prepare_variants_data_mocked, product_list, warehouses, channel_PLN, channel_USD
):
    # given
    qs = Product.objects.all()
    export_fields = {"name", "description"}
    attribute_ids = list(Attribute.objects.values_list("pk", flat=True))
    warehouse_ids = list(Warehouse.objects.values_list("pk", flat=True))
    channel_ids = [channel_PLN.pk, channel_USD.pk]

    # when
    get_variants_relations_data(
        qs, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    assert prepare_variants_data_mocked.call_count == 1
    args, kwargs = prepare_variants_data_mocked.call_args
    assert set(args[0].values_list("pk", flat=True)) == set(
        qs.values_list("pk", flat=True)
    )
    assert args[1:] == (set(), attribute_ids, warehouse_ids, channel_ids)


def test_prepare_variants_relations_data(
    product_with_variant_with_two_attributes,
    product,
    image,
    media_root,
    channel_PLN,
    channel_USD,
    file_attribute,
    product_type_page_reference_attribute,
    product_type_product_reference_attribute,
    page,
):
    # given
    product_1 = product_with_variant_with_two_attributes
    product_1.product_type.variant_attributes.add(
        file_attribute,
        product_type_page_reference_attribute,
        product_type_product_reference_attribute,
    )
    variant = product_1.variants.first()
    associate_attribute_values_to_instance(
        variant,
        {file_attribute.id: [file_attribute.values.first()]},
    )
    # add page reference attribute
    page_ref_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        reference_page=page,
        slug=f"{variant.pk}_{page.pk}",
        name=page.title,
    )
    associate_attribute_values_to_instance(
        variant,
        {product_type_page_reference_attribute.id: [page_ref_value]},
    )
    # add prodcut reference attribute
    product_ref_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        reference_product=product,
        slug=f"{variant.pk}_{product.pk}",
        name=product.name,
    )
    associate_attribute_values_to_instance(
        variant,
        {product_type_product_reference_attribute.id: [product_ref_value]},
    )

    qs = Product.objects.all()
    variant = product_with_variant_with_two_attributes.variants.first()
    product_image = ProductMedia.objects.create(
        product=product_with_variant_with_two_attributes, image=image
    )
    VariantMedia.objects.create(variant=variant, media=product_image)

    fields = {"variants__media__image"}
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()]
    warehouse_ids = [str(w.pk) for w in Warehouse.objects.all()]
    channel_ids = [str(channel_PLN.pk), str(channel_USD.pk)]

    # when
    result = prepare_variants_relations_data(
        qs, fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    expected_result = {}
    for variant in ProductVariant.objects.all():
        pk = variant.pk
        images = ", ".join(
            [
                "http://mirumee.com/media/" + image.image.name
                for image in variant.media.all()
            ]
        )
        expected_result[pk] = {"variants__media__image": images} if images else {}
        expected_result = add_variant_attribute_data_to_expected_data(
            expected_result, variant, attribute_ids, pk
        )
        expected_result = add_stocks_to_expected_data(
            expected_result, variant, warehouse_ids, pk
        )

        expected_result = add_channel_to_expected_variant_data(
            expected_result, variant, channel_ids, pk
        )

    assert result == expected_result


def test_prepare_variants_relations_data_only_fields(
    product_with_variant_with_two_attributes, image, media_root
):
    # given
    qs = Product.objects.all()
    variant = product_with_variant_with_two_attributes.variants.first()
    product_image = ProductMedia.objects.create(
        product=product_with_variant_with_two_attributes, image=image
    )
    VariantMedia.objects.create(variant=variant, media=product_image)

    fields = {"variants__media__image"}
    attribute_ids = []
    warehouse_ids = []
    channel_ids = []

    # when
    result = prepare_variants_relations_data(
        qs, fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    pk = variant.pk
    images = ", ".join(
        [
            "http://mirumee.com/media/" + image.image.name
            for image in variant.media.all()
        ]
    )
    expected_result = {pk: {"variants__media__image": images}}

    assert result == expected_result


def test_prepare_variants_relations_data_attributes_ids(
    product_with_variant_with_two_attributes, image, media_root
):
    # given
    qs = Product.objects.all()
    variant = product_with_variant_with_two_attributes.variants.first()
    product_image = ProductMedia.objects.create(
        product=product_with_variant_with_two_attributes, image=image
    )
    VariantMedia.objects.create(variant=variant, media=product_image)

    fields = set()
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()]
    warehouse_ids = []
    channel_ids = []

    # when
    result = prepare_variants_relations_data(
        qs, fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    pk = variant.pk
    expected_result = {pk: {}}

    expected_result = add_variant_attribute_data_to_expected_data(
        expected_result, variant, attribute_ids, pk
    )

    assert result == expected_result


def test_prepare_variants_relations_data_warehouse_ids(
    product_with_single_variant, image, media_root
):
    # given
    qs = Product.objects.all()
    variant = product_with_single_variant.variants.first()

    fields = set()
    attribute_ids = []
    warehouse_ids = [str(w.pk) for w in Warehouse.objects.all()]
    channel_ids = []

    # when
    result = prepare_variants_relations_data(
        qs, fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    pk = variant.pk
    expected_result = {pk: {}}

    expected_result = add_stocks_to_expected_data(
        expected_result, variant, warehouse_ids, pk
    )

    assert result == expected_result


def test_prepare_variants_relations_data_channel_ids(
    product_with_single_variant, channel_PLN, channel_USD
):
    # given
    qs = Product.objects.all()
    variant = product_with_single_variant.variants.first()

    fields = set()
    attribute_ids = []
    warehouse_ids = []
    channel_ids = [str(channel_PLN.pk), str(channel_USD.pk)]

    # when
    result = prepare_variants_relations_data(
        qs, fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    pk = variant.pk
    expected_result = {pk: {}}

    expected_result = add_channel_to_expected_variant_data(
        expected_result, variant, channel_ids, pk
    )
    assert result == expected_result


def test_add_collection_info_to_data(product):
    # given
    pk = product.pk
    collection = "test_collection"
    input_data = {pk: {}}

    # when
    result = add_collection_info_to_data(product.pk, collection, input_data)

    # then
    assert result[pk]["collections__slug"] == {collection}


def test_add_collection_info_to_data_update_collections(product):
    # given
    pk = product.pk
    existing_collection = "test2"
    collection = "test_collection"
    input_data = {pk: {"collections__slug": {existing_collection}}}

    # when
    result = add_collection_info_to_data(product.pk, collection, input_data)

    # then
    assert result[pk]["collections__slug"] == {collection, existing_collection}


def test_add_collection_info_to_data_no_collection(product):
    # given
    pk = product.pk
    collection = None
    input_data = {pk: {}}

    # when
    result = add_collection_info_to_data(product.pk, collection, input_data)

    # then
    assert result == input_data


def test_add_image_uris_to_data(product):
    # given
    pk = product.pk
    image_path = "test/path/image.jpg"
    field = "variant_media"
    input_data = {pk: {}}

    # when
    result = add_image_uris_to_data(product.pk, image_path, field, input_data)

    # then
    assert result[pk][field] == {"http://mirumee.com/media/" + image_path}


def test_add_image_uris_to_data_update_images(product):
    # given
    pk = product.pk
    old_path = "http://mirumee.com/media/test/image0.jpg"
    image_path = "test/path/image.jpg"
    input_data = {pk: {"product_media": {old_path}}}
    field = "product_media"

    # when
    result = add_image_uris_to_data(product.pk, image_path, field, input_data)

    # then
    assert result[pk][field] == {"http://mirumee.com/media/" + image_path, old_path}


def test_add_image_uris_to_data_no_image_path(product):
    # given
    pk = product.pk
    image_path = None
    input_data = {pk: {"name": "test"}}

    # when
    result = add_image_uris_to_data(product.pk, image_path, "product_media", input_data)

    # then
    assert result == input_data


def test_add_attribute_info_to_data(product):
    # given
    pk = product.pk
    slug = "test_attribute_slug"
    value_name = "test value"
    value_slug = "test-value"
    attribute_data = AttributeData(
        slug=slug,
        value_name=value_name,
        value_slug=value_slug,
        value=None,
        file_url=None,
        input_type="dropdown",
        entity_type=None,
        unit=None,
        rich_text=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{slug} (product attribute)"
    assert result[pk][expected_header] == {value_name}


def test_add_attribute_info_to_data_update_attribute_data(product):
    # given
    pk = product.pk
    slug = "test_attribute_slug"
    value_slug = "test-value"
    expected_header = f"{slug} (variant attribute)"

    attribute_data = AttributeData(
        slug=slug,
        value_slug=value_slug,
        value_name=None,
        value=None,
        file_url=None,
        input_type="dropdown",
        entity_type=None,
        unit=None,
        rich_text=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {expected_header: {"value1"}}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "variant attribute", input_data
    )

    # then
    assert result[pk][expected_header] == {value_slug, "value1"}


def test_add_attribute_info_to_data_no_slug(product):
    # given
    pk = product.pk
    attribute_data = AttributeData(
        slug=None,
        value_slug=None,
        value_name=None,
        value=None,
        file_url=None,
        input_type="dropdown",
        entity_type=None,
        unit=None,
        rich_text=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "variant attribute", input_data
    )

    # then
    assert result == input_data


def test_add_attribute_info_when_no_value(product):
    # given
    pk = product.pk
    slug = "test_attribute_slug"
    attribute_data = AttributeData(
        slug=slug,
        value_slug=None,
        value_name=None,
        value=None,
        file_url=None,
        input_type="dropdown",
        entity_type=None,
        rich_text=None,
        unit=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{slug} (product attribute)"
    assert result[pk][expected_header] == {""}


def test_add_file_attribute_info_to_data(product):
    # given
    pk = product.pk
    slug = "testtxt"
    test_url = "test.txt"
    attribute_data = AttributeData(
        slug=slug,
        value_slug=None,
        value_name=None,
        value=None,
        file_url=test_url,
        input_type="file",
        entity_type=None,
        unit=None,
        rich_text=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{slug} (product attribute)"
    assert result[pk][expected_header] == {"http://mirumee.com/media/" + test_url}


def test_add_rich_text_attribute_info_to_data(product):
    # given
    pk = product.pk
    slug = "testtxt"
    attribute_data = AttributeData(
        slug=slug,
        value_slug=None,
        value_name=None,
        value=None,
        file_url=None,
        input_type="rich-text",
        entity_type=None,
        unit=None,
        rich_text=dummy_editorjs("Dummy"),
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{slug} (product attribute)"
    assert result[pk][expected_header] == {"Dummy"}


def test_add_boolean_attribute_info_to_data(product):
    # given
    pk = product.pk
    slug = "xx_false"
    attribute_data = AttributeData(
        slug=slug,
        value=None,
        value_slug=None,
        value_name=None,
        file_url=None,
        input_type="boolean",
        entity_type=None,
        unit=None,
        rich_text=None,
        boolean=False,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{slug} (product attribute)"
    assert result[pk][expected_header] == {"False"}


def test_add_reference_attribute_info_to_data(product, page):
    # given
    pk = product.pk
    slug = "test_attribute_slug"
    value_slug = f"{product.id}_{page.id}"
    attribute_data = AttributeData(
        slug=slug,
        value_slug=value_slug,
        value_name=None,
        value=None,
        file_url=None,
        input_type="reference",
        entity_type="Page",
        unit=None,
        rich_text="None",
        boolean=None,
        date_time=None,
        reference_page=page.id,
        reference_product=None,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{slug} (product attribute)"
    assert result[pk][expected_header] == {f"Page_{page.id}"}


def test_add_reference_info_to_data_update_attribute_data(product, page):
    # given
    pk = product.pk
    slug = "test_attribute_slug"
    value_slug = f"{product.id}_{page.id}"
    expected_header = f"{slug} (variant attribute)"
    values = {"Page_989"}

    attribute_data = AttributeData(
        slug=slug,
        value_slug=value_slug,
        value_name=None,
        value=None,
        file_url=None,
        input_type="reference",
        entity_type="Page",
        unit=None,
        rich_text=None,
        boolean=None,
        date_time=None,
        reference_page=page.id,
        reference_product=None,
    )
    input_data = {pk: {expected_header: values}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "variant attribute", input_data
    )

    # then
    values.add(f"Page_{page.id}")
    assert result[pk][expected_header] == values


def test_add_date_time_attribute_info_to_data(product, date_time_attribute):
    # given
    pk = product.pk
    date_time = datetime(2021, 7, 15, 2, 3)
    attribute_data = AttributeData(
        slug=date_time_attribute.slug,
        value_slug=None,
        value_name=None,
        value=None,
        file_url=None,
        input_type="date-time",
        entity_type=None,
        unit=None,
        rich_text=None,
        boolean=None,
        date_time=date_time,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{date_time_attribute.slug} (product attribute)"
    assert result[pk][expected_header] == {f"{date_time}"}


def test_add_date_attribute_info_to_data(product, date_attribute):
    # given
    pk = product.pk
    date = datetime(2021, 8, 10, 5, 3)
    attribute_data = AttributeData(
        slug=date_attribute.slug,
        value_slug=None,
        value_name=None,
        value=None,
        file_url=None,
        input_type="date",
        entity_type=None,
        unit=None,
        rich_text=None,
        boolean=None,
        date_time=date,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{date_attribute.slug} (product attribute)"
    assert result[pk][expected_header] == {f"{date.date()}"}


def test_add_numeric_attribute_info_to_data(product, numeric_attribute):
    # given
    pk = product.pk
    name = "12.3"
    slug = "12_3"
    attribute_data = AttributeData(
        slug=numeric_attribute.slug,
        value_slug=slug,
        value_name=name,
        value=None,
        file_url=None,
        input_type="numeric",
        entity_type=None,
        unit=numeric_attribute.unit,
        rich_text=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{numeric_attribute.slug} (product attribute)"
    assert result[pk][expected_header] == {f"{name} {numeric_attribute.unit}"}


def test_add_numeric_attribute_info_to_data_no_unit(product, numeric_attribute):
    # given
    pk = product.pk
    name = "12.3"
    slug = "12_3"
    attribute_data = AttributeData(
        slug=numeric_attribute.slug,
        value_slug=slug,
        value_name=name,
        value=None,
        file_url=None,
        input_type="numeric",
        entity_type=None,
        unit=None,
        rich_text=None,
        boolean=None,
        date_time=None,
        reference_product=Product,
        reference_page=None,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{numeric_attribute.slug} (product attribute)"
    assert result[pk][expected_header] == {name}


def test_add_swatch_attribute_file_info_to_data(product, swatch_attribute):
    # given
    pk = product.pk
    slug = "white"
    value = "#ffffff"
    attribute_data = AttributeData(
        slug=swatch_attribute.slug,
        value_slug=slug,
        value_name=None,
        value=value,
        file_url=None,
        input_type="swatch",
        entity_type=None,
        unit=None,
        rich_text=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{swatch_attribute.slug} (product attribute)"
    assert result[pk][expected_header] == {value}


def test_add_attribute_info_to_data_no_file_url_for_file_attribute(product):
    # given
    pk = product.pk
    slug = "test_attribute_slug"
    value_slug = "test-value"
    attribute_data = AttributeData(
        value_slug=value_slug,
        slug=slug,
        value_name=None,
        value=None,
        file_url=None,
        input_type="file",
        entity_type=None,
        rich_text=None,
        unit=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{slug} (product attribute)"
    assert result[pk][expected_header] == {""}


def test_add_attribute_info_to_data_no_rich_text_for_rich_text_attribute(product):
    # given
    pk = product.pk
    slug = "test_attribute_slug"
    value_slug = "test-value"
    attribute_data = AttributeData(
        slug=slug,
        value_slug=value_slug,
        value=None,
        value_name=None,
        file_url=None,
        input_type="rich-text",
        entity_type=None,
        rich_text=None,
        unit=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{slug} (product attribute)"
    assert result[pk][expected_header] == {""}


def test_add_attribute_info_to_data_no_boolean_for_boolean_attribute(product):
    # given
    pk = product.pk
    slug = "xxx_None"
    attribute_data = AttributeData(
        slug=slug,
        value=None,
        value_slug=None,
        value_name=None,
        file_url=None,
        input_type="boolean",
        entity_type=None,
        rich_text=None,
        unit=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{slug} (product attribute)"
    assert result[pk][expected_header] == {""}


def test_add_attribute_info_to_data_no_value_for_reference_attribute(product):
    # given
    pk = product.pk
    slug = "test_attribute_slug"
    attribute_data = AttributeData(
        slug=slug,
        value_slug=None,
        value_name=None,
        value=None,
        file_url=None,
        input_type="reference",
        entity_type=None,
        rich_text=None,
        unit=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=None,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{slug} (product attribute)"
    assert result[pk][expected_header] == {""}


def test_add_swatch_attribute_value_info_to_data(product, numeric_attribute):
    # given
    pk = product.pk
    slug = "Logo"
    test_url = "test.txt"
    attribute_data = AttributeData(
        slug=numeric_attribute.slug,
        value_slug=slug,
        value_name=None,
        value=None,
        file_url=test_url,
        input_type="swatch",
        entity_type=None,
        unit=None,
        rich_text=None,
        boolean=None,
        date_time=None,
        reference_page=None,
        reference_product=product.id,
    )
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{numeric_attribute.slug} (product attribute)"
    assert result[pk][expected_header] == {"http://mirumee.com/media/" + test_url}


def test_add_warehouse_info_to_data(product):
    # given
    pk = product.pk
    slug = "test_warehouse"
    warehouse_data = {
        "slug": slug,
        "qty": 12,
        "qty_alc": 10,
    }
    input_data = {pk: {}}

    # when
    result = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    # then
    expected_header = f"{slug} (warehouse quantity)"
    assert result[pk][expected_header] == 12


def test_add_warehouse_info_to_data_data_not_changed(product):
    # given
    pk = product.pk
    slug = "test_warehouse"
    warehouse_data = {
        "slug": slug,
        "qty": 12,
        "qty_alc": 10,
    }
    input_data = {
        pk: {
            f"{slug} (warehouse quantity)": 5,
            f"{slug} (warehouse quantity allocated)": 8,
        }
    }

    # when
    result = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    # then
    assert result == input_data


def test_add_warehouse_info_to_data_data_no_slug(product):
    # given
    pk = product.pk
    warehouse_data = {
        "slug": None,
        "qty": None,
        "qty_alc": None,
    }
    input_data = {pk: {}}

    # when
    result = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    # then
    assert result == input_data


def test_add_channel_info_to_data(product):
    # given
    pk = product.pk
    slug = "test_channel"
    channel_data = {
        "slug": slug,
        "currency_code": "USD",
        "published": True,
    }
    input_data = {pk: {}}
    fields = ["currency_code", "published"]

    # when
    result = add_channel_info_to_data(product.pk, channel_data, input_data, fields)

    # then
    assert len(result[pk]) == 2
    assert (
        result[pk][f"{slug} (channel currency code)"] == channel_data["currency_code"]
    )
    assert result[pk][f"{slug} (channel published)"] == channel_data["published"]


def test_add_channel_info_to_data_not_changed(product):
    # given
    pk = product.pk
    slug = "test_channel"
    channel_data = {
        "slug": slug,
        "currency_code": "USD",
        "published": False,
    }
    input_data = {
        pk: {
            f"{slug} (channel currency code)": "PLN",
            f"{slug} (channel published)": True,
        }
    }
    fields = ["currency_code", "published"]

    # when
    result = add_channel_info_to_data(product.pk, channel_data, input_data, fields)

    # then
    assert result == input_data


def test_add_channel_info_to_data_no_slug(product):
    # given
    pk = product.pk
    channel_data = {
        "slug": None,
        "currency_code": None,
        "published": None,
    }
    input_data = {pk: {}}
    fields = ["currency_code"]

    # when
    result = add_channel_info_to_data(product.pk, channel_data, input_data, fields)

    # then
    assert result == input_data
