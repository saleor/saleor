import datetime

import pytest
from django.template.defaultfilters import truncatechars

from ....core.units import MeasurementUnits
from ....core.utils.editorjs import clean_editor_js
from ....tests.utils import dummy_editorjs
from ... import AttributeEntityType, AttributeInputType, AttributeType
from ...models import Attribute, AttributeValue


@pytest.fixture
def attribute_generator():
    def create_attribute(
        external_reference="attributeExtRef",
        slug="attr",
        name="Attr",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.DROPDOWN,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    ):
        attribute, _ = Attribute.objects.get_or_create(
            external_reference=external_reference,
            slug=slug,
            name=name,
            type=type,
            input_type=input_type,
            filterable_in_storefront=filterable_in_storefront,
            filterable_in_dashboard=filterable_in_dashboard,
            available_in_grid=available_in_grid,
        )

        return attribute

    return create_attribute


@pytest.fixture
def attribute_value_generator(attribute_generator):
    def create_attribute_value(
        attribute=None,
        external_reference=None,
        name="Attr Value",
        slug="attr-value",
        value="",
    ):
        if attribute is None:
            attribute = attribute_generator()
        attribute_value, _ = AttributeValue.objects.get_or_create(
            attribute=attribute,
            external_reference=external_reference,
            name=name,
            slug=slug,
            value=value,
        )

        return attribute_value

    return create_attribute_value


@pytest.fixture
def attribute_values_generator(attribute_generator):
    def create_attribute_values(
        external_references=None,
        names=None,
        slugs=None,
        attribute=None,
        values=None,
    ):
        if attribute is None:
            attribute = attribute_generator()

        if slugs is None:
            slugs = ["attr-value"]

        if external_references is None:
            external_references = [None] * len(slugs)

        if names is None:
            names = [""] * len(slugs)

        if values is None:
            values = [""] * len(slugs)

        AttributeValue.objects.bulk_create(
            [
                AttributeValue(
                    attribute=attribute,
                    external_reference=ext_ref,
                    name=name,
                    slug=slug,
                    value=value,
                )
                for slug, name, ext_ref, value in zip(
                    slugs, names, external_references, values
                )
            ],
            ignore_conflicts=True,
        )

        return list(AttributeValue.objects.filter(slug__in=slugs))

    return create_attribute_values


@pytest.fixture
def color_attribute(db, attribute_generator, attribute_values_generator):
    attribute = attribute_generator(
        external_reference="colorAttributeExternalReference",
        slug="color",
        name="Color",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    external_references = [
        "colorAttributeValue1ExternalReference",
        "colorAttributeValue2ExternalReference",
    ]
    slugs = ["red", "blue"]
    names = ["Red", "Blue"]
    attribute_values_generator(
        attribute=attribute,
        external_references=external_references,
        names=names,
        slugs=slugs,
    )

    return attribute


@pytest.fixture
def color_attribute_with_translations(db):
    attribute = Attribute.objects.create(
        slug="color",
        name="Color",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    value1 = AttributeValue.objects.create(attribute=attribute, name="Red", slug="red")
    AttributeValue.objects.create(attribute=attribute, name="Blue", slug="blue")
    attribute.translations.create(language_code="pl", name="Czerwony")
    attribute.translations.create(language_code="de", name="Rot")
    value1.translations.create(language_code="pl", plain_text="Old Kolor")
    value1.translations.create(language_code="de", name="Rot", plain_text="Old Kolor")

    return attribute


@pytest.fixture
def attribute_without_values():
    return Attribute.objects.create(
        slug="dropdown",
        name="Dropdown",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
        visible_in_storefront=True,
        entity_type=None,
    )


@pytest.fixture
def multiselect_attribute(db, attribute_generator, attribute_values_generator):
    attribute = attribute_generator(
        slug="multi",
        name="Multi",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.MULTISELECT,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    slugs = ["choice-1", "choice-1"]
    names = ["Choice 1", "Choice 2"]
    attribute_values_generator(
        attribute=attribute,
        names=names,
        slugs=slugs,
    )

    return attribute


@pytest.fixture
def date_attribute(db):
    attribute = Attribute.objects.create(
        slug="release-date",
        name="Release date",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.DATE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=attribute,
                name=f"{attribute.name}: {value.date()}",
                slug=f"{value.date()}_{attribute.id}",
                date_time=value,
            )
            for value in [
                datetime.datetime(2020, 10, 5, tzinfo=datetime.UTC),
                datetime.datetime(2020, 11, 5, tzinfo=datetime.UTC),
            ]
        ]
    )

    return attribute


@pytest.fixture
def date_time_attribute(db):
    attribute = Attribute.objects.create(
        slug="release-date-time",
        name="Release date time",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.DATE_TIME,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )

    AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=attribute,
                name=f"{attribute.name}: {value.date()}",
                slug=f"{value.date()}_{attribute.id}",
                date_time=value,
            )
            for value in [
                datetime.datetime(2020, 10, 5, tzinfo=datetime.UTC),
                datetime.datetime(2020, 11, 5, tzinfo=datetime.UTC),
            ]
        ]
    )

    return attribute


@pytest.fixture
def attribute_choices_for_sorting(db):
    attribute = Attribute.objects.create(
        slug="sorting",
        name="Sorting",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="Global", slug="summer")
    AttributeValue.objects.create(attribute=attribute, name="Apex", slug="zet")
    AttributeValue.objects.create(attribute=attribute, name="Police", slug="absorb")
    return attribute


@pytest.fixture
def boolean_attribute(db):
    attribute = Attribute.objects.create(
        slug="boolean",
        name="Boolean",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.BOOLEAN,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name=f"{attribute.name}: Yes",
        slug=f"{attribute.id}_true",
        boolean=True,
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name=f"{attribute.name}: No",
        slug=f"{attribute.id}_false",
        boolean=False,
    )
    return attribute


@pytest.fixture
def rich_text_attribute(db):
    attribute = Attribute.objects.create(
        slug="text",
        name="Text",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.RICH_TEXT,
        filterable_in_storefront=False,
        filterable_in_dashboard=False,
        available_in_grid=False,
    )
    text = "Rich text attribute content."
    AttributeValue.objects.create(
        attribute=attribute,
        name=truncatechars(clean_editor_js(dummy_editorjs(text), to_string=True), 50),
        slug=f"instance_{attribute.id}",
        rich_text=dummy_editorjs(text),
    )
    return attribute


@pytest.fixture
def rich_text_attribute_page_type(db):
    attribute = Attribute.objects.create(
        slug="text",
        name="Text",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.RICH_TEXT,
        filterable_in_storefront=False,
        filterable_in_dashboard=False,
        available_in_grid=False,
    )
    text = "Rich text attribute content."
    AttributeValue.objects.create(
        attribute=attribute,
        name=truncatechars(clean_editor_js(dummy_editorjs(text), to_string=True), 50),
        slug=f"instance_{attribute.id}",
        rich_text=dummy_editorjs(text),
    )
    return attribute


@pytest.fixture
def rich_text_attribute_with_many_values(rich_text_attribute):
    attribute = rich_text_attribute
    values = []
    for i in range(5):
        text = f"Rich text attribute content{i}."
        values.append(
            AttributeValue(
                attribute=attribute,
                name=truncatechars(
                    clean_editor_js(dummy_editorjs(text), to_string=True), 50
                ),
                slug=f"instance_{attribute.id}_{i}",
                rich_text=dummy_editorjs(text),
            )
        )
    AttributeValue.objects.bulk_create(values)
    return rich_text_attribute


@pytest.fixture
def plain_text_attribute(db):
    attribute = Attribute.objects.create(
        slug="plain-text",
        name="Plain text",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.PLAIN_TEXT,
        filterable_in_storefront=False,
        filterable_in_dashboard=False,
        available_in_grid=False,
    )
    text = "Plain text attribute content."
    AttributeValue.objects.create(
        attribute=attribute,
        name=truncatechars(text, 50),
        slug=f"instance_{attribute.id}",
        plain_text=text,
    )
    return attribute


@pytest.fixture
def plain_text_attribute_page_type(db):
    attribute = Attribute.objects.create(
        slug="plain-text",
        name="Plain text",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.PLAIN_TEXT,
        filterable_in_storefront=False,
        filterable_in_dashboard=False,
        available_in_grid=False,
    )
    text = "Plain text attribute content."
    AttributeValue.objects.create(
        attribute=attribute,
        name=truncatechars(text, 50),
        slug=f"instance_{attribute.id}",
        plain_text=text,
    )
    return attribute


@pytest.fixture
def color_attribute_without_values(db):  # pylint: disable=W0613
    return Attribute.objects.create(
        slug="color",
        name="Color",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )


@pytest.fixture
def pink_attribute_value(color_attribute):  # pylint: disable=W0613
    value = AttributeValue.objects.create(
        slug="pink", name="Pink", attribute=color_attribute, value="#FF69B4"
    )
    return value


@pytest.fixture
def size_attribute(db, attribute_generator, attribute_values_generator):  # pylint: disable=W0613
    attribute = attribute_generator(
        external_reference="sizeAttributeExternalReference",
        slug="size",
        name="Size",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )

    slugs = ["small", "big"]
    names = ["Small", "Big"]
    attribute_values_generator(
        attribute=attribute,
        names=names,
        slugs=slugs,
    )

    return attribute


@pytest.fixture
def weight_attribute(db):
    attribute = Attribute.objects.create(
        slug="material",
        name="Material",
        type=AttributeType.PRODUCT_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="Cotton", slug="cotton")
    AttributeValue.objects.create(
        attribute=attribute, name="Poliester", slug="poliester"
    )
    return attribute


@pytest.fixture
def numeric_attribute(db):
    attribute = Attribute.objects.create(
        slug="length",
        name="Length",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.NUMERIC,
        unit=MeasurementUnits.CM,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="9.5", slug="10_5")
    AttributeValue.objects.create(attribute=attribute, name="15.2", slug="15_2")
    return attribute


@pytest.fixture
def numeric_attribute_without_unit(db):
    attribute = Attribute.objects.create(
        slug="count",
        name="Count",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.NUMERIC,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="9", slug="9")
    AttributeValue.objects.create(attribute=attribute, name="15", slug="15")
    return attribute


@pytest.fixture
def file_attribute(db):
    attribute = Attribute.objects.create(
        slug="image",
        name="Image",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.FILE,
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="test_file.txt",
        slug="test_filetxt",
        file_url="test_file.txt",
        content_type="text/plain",
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="test_file.jpeg",
        slug="test_filejpeg",
        file_url="test_file.jpeg",
        content_type="image/jpeg",
    )
    return attribute


@pytest.fixture
def file_attribute_with_file_input_type_without_values(db):
    return Attribute.objects.create(
        slug="image",
        name="Image",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.FILE,
    )


@pytest.fixture
def swatch_attribute(db):
    attribute = Attribute.objects.create(
        slug="T-shirt color",
        name="t-shirt-color",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.SWATCH,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(
        attribute=attribute, name="Red", slug="red", value="#ff0000"
    )
    AttributeValue.objects.create(
        attribute=attribute, name="White", slug="whit", value="#fffff"
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="Logo",
        slug="logo",
        file_url="http://mirumee.com/test_media/test_file.jpeg",
        content_type="image/jpeg",
    )
    return attribute


@pytest.fixture
def product_type_page_reference_attribute(db):
    return Attribute.objects.create(
        slug="page-reference",
        name="Page reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PAGE,
    )


@pytest.fixture
def page_type_page_reference_attribute(db):
    return Attribute.objects.create(
        slug="page-reference",
        name="Page reference",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PAGE,
    )


@pytest.fixture
def product_type_product_reference_attribute(db):
    return Attribute.objects.create(
        slug="product-reference",
        name="Product reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT,
    )


@pytest.fixture
def page_type_product_reference_attribute(db):
    return Attribute.objects.create(
        slug="product-reference",
        name="Product reference",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT,
    )


@pytest.fixture
def product_type_variant_reference_attribute(db):
    return Attribute.objects.create(
        slug="variant-reference",
        name="Variant reference",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT_VARIANT,
    )


@pytest.fixture
def page_type_variant_reference_attribute(db):
    return Attribute.objects.create(
        slug="variant-reference",
        name="Variant reference",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.REFERENCE,
        entity_type=AttributeEntityType.PRODUCT_VARIANT,
    )


@pytest.fixture
def size_page_attribute(db):
    attribute = Attribute.objects.create(
        slug="page-size",
        name="Page size",
        type=AttributeType.PAGE_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="10", slug="10")
    AttributeValue.objects.create(attribute=attribute, name="15", slug="15")
    return attribute


@pytest.fixture
def tag_page_attribute(db):
    attribute = Attribute.objects.create(
        slug="tag",
        name="tag",
        type=AttributeType.PAGE_TYPE,
        filterable_in_storefront=True,
        filterable_in_dashboard=True,
        available_in_grid=True,
    )
    AttributeValue.objects.create(attribute=attribute, name="About", slug="about")
    AttributeValue.objects.create(attribute=attribute, name="Help", slug="help")
    return attribute


@pytest.fixture
def author_page_attribute(db):
    attribute = Attribute.objects.create(
        slug="author", name="author", type=AttributeType.PAGE_TYPE
    )
    AttributeValue.objects.create(
        attribute=attribute, name="Test author 1", slug="test-author-1"
    )
    AttributeValue.objects.create(
        attribute=attribute, name="Test author 2", slug="test-author-2"
    )
    return attribute


@pytest.fixture
def page_file_attribute(db):
    attribute = Attribute.objects.create(
        slug="image",
        name="Image",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.FILE,
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="test_file.txt",
        slug="test_filetxt",
        file_url="test_file.txt",
        content_type="text/plain",
    )
    AttributeValue.objects.create(
        attribute=attribute,
        name="test_file.jpeg",
        slug="test_filejpeg",
        file_url="test_file.jpeg",
        content_type="image/jpeg",
    )
    return attribute


@pytest.fixture
def product_type_attribute_list() -> list[Attribute]:
    return list(
        Attribute.objects.bulk_create(
            [
                Attribute(
                    slug="height", name="Height", type=AttributeType.PRODUCT_TYPE
                ),
                Attribute(
                    slug="weight", name="Weight", type=AttributeType.PRODUCT_TYPE
                ),
                Attribute(
                    slug="thickness", name="Thickness", type=AttributeType.PRODUCT_TYPE
                ),
            ]
        )
    )


@pytest.fixture
def page_type_attribute_list() -> list[Attribute]:
    return list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="size", name="Size", type=AttributeType.PAGE_TYPE),
                Attribute(slug="font", name="Weight", type=AttributeType.PAGE_TYPE),
                Attribute(
                    slug="margin", name="Thickness", type=AttributeType.PAGE_TYPE
                ),
            ]
        )
    )
