import json

import graphene
from measurement.measures import Weight

from .....attribute.models import Attribute, AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....channel.models import Channel
from .....product.models import Product, ProductVariant, VariantMedia
from .....warehouse.models import Warehouse
from ....utils import ProductExportFields
from ....utils.products_data import get_products_data
from .utils import (
    add_channel_to_expected_product_data,
    add_channel_to_expected_variant_data,
    add_product_attribute_data_to_expected_data,
    add_stocks_to_expected_data,
    add_variant_attribute_data_to_expected_data,
)


def test_get_products_data(product, product_with_image, collection, image, channel_USD):
    # given
    product.description = {
        "blocks": [
            {"data": {"text": "This is an example description."}, "type": "paragraph"}
        ]
    }
    product.weight = Weight(kg=5)
    product.save(update_fields=["description", "weight"])

    collection.products.add(product)

    variant = product.variants.first()
    VariantMedia.objects.create(variant=variant, media=product.media.first())

    variant_without_sku = product.variants.last()
    variant_without_sku.sku = None
    variant_without_sku.save()

    products = Product.objects.all()
    export_fields = set(
        value
        for mapping in ProductExportFields.HEADERS_TO_FIELDS_MAPPING.values()
        for value in mapping.values()
    )
    warehouse_ids = [str(warehouse.pk) for warehouse in Warehouse.objects.all()]
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()]
    channel_ids = [str(channel.pk) for channel in Channel.objects.all()]

    variants = []
    for variant in product.variants.all():
        for attr in variant.attributes.all():
            attribute_ids.append(str(attr.assignment.attribute.pk))
        variant.weight = Weight(kg=3)
        variants.append(variant)

    ProductVariant.objects.bulk_update(variants, ["weight"])

    variants = []
    for variant in product_with_image.variants.all():
        variant.weight = None
        variants.append(variant)
    ProductVariant.objects.bulk_update(variants, ["weight"])

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        id = graphene.Node.to_global_id("Product", product.pk)
        product_data = {
            "id": id,
            "name": product.name,
            "description_as_str": json.dumps(product.description),
            "category__slug": product.category.slug,
            "product_type__name": product.product_type.name,
            "charge_taxes": product.charge_taxes,
            "collections__slug": (
                ""
                if not product.collections.all()
                else product.collections.first().slug
            ),
            "product_weight": (
                "{} g".format(int(product.weight.value)) if product.weight else ""
            ),
            "media__image": (
                ""
                if not product.media.all()
                else "http://mirumee.com{}".format(product.media.first().image.url)
            ),
        }

        product_data = add_product_attribute_data_to_expected_data(
            product_data, product, attribute_ids
        )
        product_data = add_channel_to_expected_product_data(
            product_data, product, channel_ids
        )

        for variant in product.variants.all():
            data = {
                "variants__id": graphene.Node.to_global_id(
                    "ProductVariant", variant.pk
                ),
                "variants__sku": variant.sku,
                "variants__media__image": (
                    ""
                    if not variant.media.all()
                    else "http://mirumee.com{}".format(variant.media.first().image.url)
                ),
                "variant_weight": (
                    "{} g".foramt(int(variant.weight.value)) if variant.weight else ""
                ),
                "variants__is_preorder": variant.is_preorder,
                "variants__preorder_global_threshold": (
                    variant.preorder_global_threshold
                ),
                "variants__preorder_end_date": variant.preorder_end_date,
            }
            data.update(product_data)

            data = add_stocks_to_expected_data(data, variant, warehouse_ids)
            data = add_variant_attribute_data_to_expected_data(
                data, variant, attribute_ids
            )
            data = add_channel_to_expected_variant_data(data, variant, channel_ids)

            expected_data.append(data)
    assert result_data == expected_data


def test_get_products_data_for_specified_attributes(
    product, product_with_variant_with_two_attributes
):
    # given
    products = Product.objects.all()
    export_fields = {"id", "variants__sku"}
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()][:1]
    warehouse_ids = []
    channel_ids = []

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        id = graphene.Node.to_global_id("Product", product.pk)
        product_data = {"id": id}

        product_data = add_product_attribute_data_to_expected_data(
            product_data, product, attribute_ids
        )

        for variant in product.variants.all():
            data = {}
            data.update(product_data)
            data["variants__sku"] = variant.sku
            data = add_variant_attribute_data_to_expected_data(
                data, variant, attribute_ids
            )

            expected_data.append(data)

    assert result_data == expected_data


def test_get_products_data_for_specified_warehouses(
    product, product_with_image, variant_with_many_stocks
):
    # given
    product.variants.add(variant_with_many_stocks)

    products = Product.objects.all()
    export_fields = {"id", "variants__sku"}
    warehouse_ids = [str(warehouse.pk) for warehouse in Warehouse.objects.all()][:2]
    attribute_ids = []
    channel_ids = []

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        id = graphene.Node.to_global_id("Product", product.pk)
        product_data = {"id": id}

        for variant in product.variants.all():
            data = {"variants__sku": variant.sku}
            data.update(product_data)

            data = add_stocks_to_expected_data(data, variant, warehouse_ids)

            expected_data.append(data)
    for res in result_data:
        assert res in expected_data


def test_get_products_data_for_product_without_channel(
    product, product_with_image, variant_with_many_stocks
):
    # given
    product.variants.add(variant_with_many_stocks)
    product_with_image.channel_listings.all().delete()

    products = Product.objects.all()
    export_fields = {"id", "variants__sku"}
    warehouse_ids = []
    attribute_ids = []
    channel_ids = []

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        id = graphene.Node.to_global_id("Product", product.pk)
        product_data = {"id": id}

        for variant in product.variants.all():
            data = {"variants__sku": variant.sku}
            data.update(product_data)

            data = add_stocks_to_expected_data(data, variant, warehouse_ids)

            expected_data.append(data)

    for res in result_data:
        assert res in expected_data


def test_get_products_data_for_specified_warehouses_channels_and_attributes(
    file_attribute,
    page_list,
    product,
    variant,
    product_type_page_reference_attribute,
    product_type_product_reference_attribute,
    product_type_variant_reference_attribute,
    numeric_attribute,
    product_with_image,
    product_with_variant_with_two_attributes,
    rich_text_attribute,
    color_attribute,
    boolean_attribute,
    date_attribute,
    date_time_attribute,
    variant_with_many_stocks,
    swatch_attribute,
):
    # given
    product.variants.add(variant_with_many_stocks)
    product.product_type.variant_attributes.add(
        file_attribute,
        product_type_page_reference_attribute,
        product_type_product_reference_attribute,
        product_type_variant_reference_attribute,
        numeric_attribute,
        rich_text_attribute,
        swatch_attribute,
        boolean_attribute,
        date_attribute,
        date_time_attribute,
    )
    product.product_type.product_attributes.add(
        file_attribute,
        product_type_page_reference_attribute,
        product_type_product_reference_attribute,
        product_type_variant_reference_attribute,
        numeric_attribute,
        rich_text_attribute,
        swatch_attribute,
        boolean_attribute,
        date_attribute,
        date_time_attribute,
    )

    variant_without_sku = product.variants.last()
    variant_without_sku.sku = None
    variant_without_sku.save()

    # add boolean attribute
    associate_attribute_values_to_instance(
        variant_with_many_stocks,
        boolean_attribute,
        boolean_attribute.values.first(),
    )
    associate_attribute_values_to_instance(
        product, boolean_attribute, boolean_attribute.values.first()
    )

    # add date attribute
    associate_attribute_values_to_instance(
        variant_with_many_stocks,
        date_attribute,
        date_attribute.values.first(),
    )
    associate_attribute_values_to_instance(
        product, date_attribute, date_attribute.values.first()
    )

    # add date time attribute
    associate_attribute_values_to_instance(
        variant_with_many_stocks,
        date_time_attribute,
        date_time_attribute.values.first(),
    )
    associate_attribute_values_to_instance(
        product, date_time_attribute, date_time_attribute.values.first()
    )

    # add rich text attribute
    associate_attribute_values_to_instance(
        variant_with_many_stocks,
        rich_text_attribute,
        rich_text_attribute.values.first(),
    )
    associate_attribute_values_to_instance(
        product, rich_text_attribute, rich_text_attribute.values.first()
    )

    # add page reference attribute
    product_page_ref_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        reference_page=page_list[0],
        slug=f"{product.pk}_{page_list[0].pk}",
        name=page_list[0].title,
    )
    variant_page_ref_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        reference_page=page_list[1],
        slug=f"{variant_with_many_stocks.pk}_{page_list[1].pk}",
        name=page_list[1].title,
    )
    associate_attribute_values_to_instance(
        variant_with_many_stocks,
        product_type_page_reference_attribute,
        variant_page_ref_value,
    )
    associate_attribute_values_to_instance(
        product, product_type_page_reference_attribute, product_page_ref_value
    )

    # add product reference attribute
    variant_product_ref_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        reference_product=product_with_variant_with_two_attributes,
        slug=(
            f"{variant_with_many_stocks.pk}"
            f"_{product_with_variant_with_two_attributes.pk}"
        ),
        name=product_with_variant_with_two_attributes.name,
    )
    product_product_ref_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        reference_product=product_with_image,
        slug=f"{product.pk}_{product_with_image.pk}",
        name=product_with_image.name,
    )
    associate_attribute_values_to_instance(
        variant_with_many_stocks,
        product_type_product_reference_attribute,
        variant_product_ref_value,
    )
    associate_attribute_values_to_instance(
        product, product_type_product_reference_attribute, product_product_ref_value
    )

    # add variant reference attribute
    variant_variant_ref_value = AttributeValue.objects.create(
        attribute=product_type_variant_reference_attribute,
        reference_variant=variant,
        slug=(f"{variant_with_many_stocks.pk}" f"_{variant.pk}"),
        name=variant.name,
    )
    product_variant_ref_value = AttributeValue.objects.create(
        attribute=product_type_variant_reference_attribute,
        reference_variant=variant,
        slug=f"{product.pk}_{variant.pk}",
        name=variant.name,
    )
    associate_attribute_values_to_instance(
        variant_with_many_stocks,
        product_type_variant_reference_attribute,
        variant_variant_ref_value,
    )
    associate_attribute_values_to_instance(
        product, product_type_variant_reference_attribute, product_variant_ref_value
    )

    # add numeric attribute
    numeric_value_1 = numeric_attribute.values.first()
    numeric_value_2 = numeric_attribute.values.last()

    associate_attribute_values_to_instance(
        variant_with_many_stocks, numeric_attribute, numeric_value_1
    )
    associate_attribute_values_to_instance(product, numeric_attribute, numeric_value_2)

    # create assigned product without values
    associate_attribute_values_to_instance(
        product, color_attribute, color_attribute.values.first()
    )
    assigned_product = product.attributes.get(assignment__attribute=color_attribute)
    assigned_product.values.clear()

    # add swatch attribute
    swatch_value_1 = swatch_attribute.values.first()
    swatch_value_2 = swatch_attribute.values.last()

    associate_attribute_values_to_instance(
        variant_with_many_stocks, swatch_attribute, swatch_value_1
    )
    associate_attribute_values_to_instance(product, swatch_attribute, swatch_value_2)

    products = Product.objects.all()
    export_fields = {"id", "variants__sku"}
    warehouse_ids = [str(warehouse.pk) for warehouse in Warehouse.objects.all()]
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()]
    channel_ids = [str(channel.pk) for channel in Channel.objects.all()]

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        id = graphene.Node.to_global_id("Product", product.pk)
        product_data = {"id": id}

        product_data = add_product_attribute_data_to_expected_data(
            product_data, product, attribute_ids
        )
        product_data = add_channel_to_expected_product_data(
            product_data, product, channel_ids
        )

        for variant in product.variants.all():
            data = {"variants__sku": variant.sku}
            data.update(product_data)

            data = add_stocks_to_expected_data(data, variant, warehouse_ids)
            data = add_variant_attribute_data_to_expected_data(
                data, variant, attribute_ids
            )
            data = add_channel_to_expected_variant_data(data, variant, channel_ids)

            expected_data.append(data)

    assert result_data == expected_data
