from saleor.attribute import AttributeType
from saleor.attribute.models import Attribute, AttributeValue


def test_attribute_value_setting_up_max_sort_oder():
    # given
    attribute = Attribute.objects.create(
        slug="test-slug",
        name="test name",
        type=AttributeType.PRODUCT_TYPE,
    )
    assert attribute.max_sort_order is None

    # when
    attribute_value = AttributeValue.objects.create(
        attribute=attribute, name="value", slug="value"
    )

    # then
    assert attribute_value.sort_order == 1
    assert attribute.max_sort_order == 1


def test_attribute_value_using_max_sort_order_from_parent():
    # given
    attribute = Attribute.objects.create(
        slug="test-slug",
        name="test name",
        type=AttributeType.PRODUCT_TYPE,
        max_sort_order=1337,
    )
    assert attribute.max_sort_order == 1337

    # when
    attribute_value = AttributeValue.objects.create(
        attribute=attribute, name="value", slug="value"
    )

    # then
    assert attribute_value.sort_order == 1338
    assert attribute.max_sort_order == 1338


def test_attribute_value_sort_order_when_attribute_has_other_values():
    # given
    attribute = Attribute.objects.create(
        slug="test-slug",
        name="test name",
        type=AttributeType.PRODUCT_TYPE,
    )
    AttributeValue.objects.create(
        attribute=attribute, name="value", slug="value", sort_order=1
    )
    assert attribute.max_sort_order == 1

    # when
    attribute_value = AttributeValue.objects.create(
        attribute=attribute, name="value2", slug="value2"
    )

    # then
    assert attribute_value.sort_order == 2
    assert attribute.max_sort_order == 2


def test_max_sort_order_when_deleting_attribute_value():
    # given
    attribute = Attribute.objects.create(
        slug="test-slug",
        name="test name",
        type=AttributeType.PRODUCT_TYPE,
    )
    value = AttributeValue.objects.create(
        attribute=attribute, name="value", slug="value", sort_order=1
    )
    value2 = AttributeValue.objects.create(
        attribute=attribute, name="value2", slug="value2", sort_order=2
    )
    assert attribute.max_sort_order == 2

    # when
    value.delete()

    # then
    attribute.refresh_from_db()
    assert attribute.max_sort_order == 1
    value2.refresh_from_db()
    assert value2.sort_order == 1
