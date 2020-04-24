from datetime import timedelta
from decimal import Decimal

import graphene
import pytest
from django.utils import timezone
from django_countries import countries

from saleor.discount import DiscountValueType, VoucherType
from saleor.discount.error_codes import DiscountErrorCode
from saleor.discount.models import Sale, Voucher
from saleor.graphql.discount.enums import DiscountValueTypeEnum, VoucherTypeEnum
from tests.api.utils import get_graphql_content


@pytest.fixture
def voucher_countries(voucher):
    voucher.countries = countries
    voucher.save(update_fields=["countries"])
    return voucher


@pytest.fixture
def query_vouchers_with_filter():
    query = """
    query ($filter: VoucherFilterInput!, ) {
      vouchers(first:5, filter: $filter){
        edges{
          node{
            id
            name
            startDate
          }
        }
      }
    }
    """
    return query


@pytest.fixture
def query_sales_with_filter():
    query = """
    query ($filter: SaleFilterInput!, ) {
      sales(first:5, filter: $filter){
        edges{
          node{
            id
            name
            startDate
          }
        }
      }
    }
    """
    return query


@pytest.fixture
def sale():
    return Sale.objects.create(name="Sale", value=123)


@pytest.fixture
def voucher():
    return Voucher.objects.create(name="Voucher", discount_value=123)


def test_voucher_query(
    staff_api_client, voucher_countries, permission_manage_discounts
):
    query = """
    query vouchers {
        vouchers(first: 1) {
            edges {
                node {
                    type
                    name
                    code
                    usageLimit
                    used
                    startDate
                    discountValueType
                    discountValue
                    applyOncePerCustomer
                    countries {
                        code
                        country
                    }
                }
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"][0]["node"]

    assert data["type"] == voucher_countries.type.upper()
    assert data["name"] == voucher_countries.name
    assert data["code"] == voucher_countries.code
    assert data["usageLimit"] == voucher_countries.usage_limit
    assert data["applyOncePerCustomer"] == voucher_countries.apply_once_per_customer
    assert data["used"] == voucher_countries.used
    assert data["startDate"] == voucher_countries.start_date.isoformat()
    assert data["discountValueType"] == voucher_countries.discount_value_type.upper()
    assert data["discountValue"] == voucher_countries.discount_value
    assert data["countries"] == [
        {"country": country.name, "code": country.code}
        for country in voucher_countries.countries
    ]


def test_sale_query(staff_api_client, sale, permission_manage_discounts):
    query = """
        query sales {
            sales(first: 1) {
                edges {
                    node {
                        type
                        name
                        value
                        startDate
                    }
                }
            }
        }
        """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"][0]["node"]
    assert data["type"] == sale.type.upper()
    assert data["name"] == sale.name
    assert data["value"] == sale.value
    assert data["startDate"] == sale.start_date.isoformat()


CREATE_VOUCHER_MUTATION = """
mutation  voucherCreate(
    $type: VoucherTypeEnum, $name: String, $code: String,
    $discountValueType: DiscountValueTypeEnum, $usageLimit: Int,
    $discountValue: Decimal, $minAmountSpent: Decimal, $minCheckoutItemsQuantity: Int,
    $startDate: DateTime, $endDate: DateTime, $applyOncePerOrder: Boolean,
    $applyOncePerCustomer: Boolean) {
        voucherCreate(input: {
                name: $name, type: $type, code: $code,
                discountValueType: $discountValueType,
                discountValue: $discountValue, minAmountSpent: $minAmountSpent,
                minCheckoutItemsQuantity: $minCheckoutItemsQuantity,
                startDate: $startDate, endDate: $endDate, usageLimit: $usageLimit
                applyOncePerOrder: $applyOncePerOrder,
                applyOncePerCustomer: $applyOncePerCustomer}) {
            discountErrors {
                field
                code
                message
            }
            voucher {
                type
                minSpent {
                    amount
                }
                minCheckoutItemsQuantity
                name
                code
                discountValueType
                startDate
                endDate
                applyOncePerOrder
                applyOncePerCustomer
            }
        }
    }
"""


def test_create_voucher(staff_api_client, permission_manage_discounts):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": "testcode123",
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minAmountSpent": 1.12,
        "minCheckoutItemsQuantity": 10,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "applyOncePerOrder": True,
        "applyOncePerCustomer": True,
        "usageLimit": 3,
    }

    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    get_graphql_content(response)
    voucher = Voucher.objects.get()
    assert voucher.type == VoucherType.ENTIRE_ORDER
    assert voucher.min_spent_amount == Decimal("1.12")
    assert voucher.name == "test voucher"
    assert voucher.code == "testcode123"
    assert voucher.discount_value_type == DiscountValueType.FIXED
    assert voucher.start_date == start_date
    assert voucher.end_date == end_date
    assert voucher.apply_once_per_order
    assert voucher.apply_once_per_customer
    assert voucher.usage_limit == 3


def test_create_voucher_with_empty_code(staff_api_client, permission_manage_discounts):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": "",
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minSpent": 1.12,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": None,
    }

    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]["voucher"]
    assert data["name"] == variables["name"]
    assert data["code"] != ""


def test_create_voucher_with_existing_gift_card_code(
    staff_api_client, gift_card, permission_manage_discounts
):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": gift_card.code,
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minAmountSpent": 1.12,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": 3,
    }

    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["voucherCreate"]["discountErrors"]
    errors = content["data"]["voucherCreate"]["discountErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "code"
    assert errors[0]["code"] == DiscountErrorCode.ALREADY_EXISTS.name


def test_create_voucher_with_existing_voucher_code(
    staff_api_client, voucher_shipping_type, permission_manage_discounts
):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": voucher_shipping_type.code,
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minAmountSpent": 1.12,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": 3,
    }
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["voucherCreate"]["discountErrors"]
    errors = content["data"]["voucherCreate"]["discountErrors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "code"
    assert errors


def test_update_voucher(staff_api_client, voucher, permission_manage_discounts):
    query = """
    mutation  voucherUpdate($code: String,
        $discountValueType: DiscountValueTypeEnum, $id: ID!,
        $applyOncePerOrder: Boolean, $minCheckoutItemsQuantity: Int) {
            voucherUpdate(id: $id, input: {
                code: $code, discountValueType: $discountValueType,
                applyOncePerOrder: $applyOncePerOrder,
                minCheckoutItemsQuantity: $minCheckoutItemsQuantity
                }) {
                discountErrors {
                    field
                    code
                    message
                }
                voucher {
                    code
                    discountValueType
                    applyOncePerOrder
                    minCheckoutItemsQuantity
                }
            }
        }
    """
    apply_once_per_order = not voucher.apply_once_per_order
    # Set discount value type to 'fixed' and change it in mutation
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save()
    assert voucher.code != "testcode123"
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "code": "testcode123",
        "discountValueType": DiscountValueTypeEnum.PERCENTAGE.name,
        "applyOncePerOrder": apply_once_per_order,
        "minCheckoutItemsQuantity": 10,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherUpdate"]["voucher"]
    assert data["code"] == "testcode123"
    assert data["discountValueType"] == DiscountValueType.PERCENTAGE.upper()
    assert data["applyOncePerOrder"] == apply_once_per_order
    assert data["minCheckoutItemsQuantity"] == 10


def test_voucher_delete_mutation(
    staff_api_client, voucher, permission_manage_discounts
):
    query = """
        mutation DeleteVoucher($id: ID!) {
            voucherDelete(id: $id) {
                voucher {
                    name
                    id
                }
                discountErrors {
                    field
                    code
                    message
                }
              }
            }
    """
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.id)}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherDelete"]
    assert data["voucher"]["name"] == voucher.name
    with pytest.raises(voucher._meta.model.DoesNotExist):
        voucher.refresh_from_db()


def test_voucher_add_catalogues(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    permission_manage_discounts,
):
    query = """
        mutation voucherCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            voucherCataloguesAdd(id: $id, input: $input) {
                discountErrors {
                    field
                    code
                    message
                }
            }
        }
    """
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesAdd"]

    assert not data["discountErrors"]
    assert product in voucher.products.all()
    assert category in voucher.categories.all()
    assert collection in voucher.collections.all()


def test_voucher_remove_catalogues(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    permission_manage_discounts,
):
    voucher.products.add(product)
    voucher.collections.add(collection)
    voucher.categories.add(category)

    query = """
        mutation voucherCataloguesRemove($id: ID!, $input: CatalogueInput!) {
            voucherCataloguesRemove(id: $id, input: $input) {
                discountErrors {
                    field
                    code
                    message
                }
            }
        }
    """
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesRemove"]

    assert not data["discountErrors"]
    assert product not in voucher.products.all()
    assert category not in voucher.categories.all()
    assert collection not in voucher.collections.all()


def test_voucher_add_no_catalogues(
    staff_api_client, voucher, permission_manage_discounts
):
    query = """
        mutation voucherCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            voucherCataloguesAdd(id: $id, input: $input) {
                discountErrors {
                    field
                    code
                    message
                }
            }
        }
    """
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {"products": [], "collections": [], "categories": []},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesAdd"]

    assert not data["discountErrors"]
    assert not voucher.products.exists()
    assert not voucher.categories.exists()
    assert not voucher.collections.exists()


def test_voucher_remove_no_catalogues(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    permission_manage_discounts,
):
    voucher.products.add(product)
    voucher.collections.add(collection)
    voucher.categories.add(category)

    query = """
            mutation voucherCataloguesAdd($id: ID!, $input: CatalogueInput!) {
                voucherCataloguesAdd(id: $id, input: $input) {
                    discountErrors {
                        field
                        code
                        message
                    }
                }
            }
        """
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {"products": [], "collections": [], "categories": []},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesAdd"]

    assert not data["discountErrors"]
    assert voucher.products.exists()
    assert voucher.categories.exists()
    assert voucher.collections.exists()


def test_create_sale(staff_api_client, permission_manage_discounts):
    query = """
    mutation  saleCreate(
            $type: DiscountValueTypeEnum, $name: String, $value: Decimal,
            $startDate: DateTime, $endDate: DateTime) {
        saleCreate(input: {
                name: $name, type: $type, value: $value,
                startDate: $startDate, endDate: $endDate}) {
            sale {
                type
                name
                value
                startDate
                endDate
            }
            discountErrors {
                field
                code
                message
            }
        }
    }
    """
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test sale",
        "type": DiscountValueTypeEnum.FIXED.name,
        "value": "10.12",
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["saleCreate"]["sale"]

    assert data["type"] == DiscountValueType.FIXED.upper()
    assert data["name"] == "test sale"
    assert data["value"] == 10.12
    assert data["startDate"] == start_date.isoformat()
    assert data["endDate"] == end_date.isoformat()


def test_update_sale(staff_api_client, sale, permission_manage_discounts):
    query = """
    mutation  saleUpdate($type: DiscountValueTypeEnum, $id: ID!) {
            saleUpdate(id: $id, input: {type: $type}) {
                discountErrors {
                    field
                    code
                    message
                }
                sale {
                    type
                }
            }
        }
    """
    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    sale.save()
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "type": DiscountValueTypeEnum.PERCENTAGE.name,
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["saleUpdate"]["sale"]
    assert data["type"] == DiscountValueType.PERCENTAGE.upper()


def test_sale_delete_mutation(staff_api_client, sale, permission_manage_discounts):
    query = """
        mutation DeleteSale($id: ID!) {
            saleDelete(id: $id) {
                sale {
                    name
                    id
                }
                discountErrors {
                    field
                    code
                    message
                }
              }
            }
    """
    variables = {"id": graphene.Node.to_global_id("Sale", sale.id)}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["saleDelete"]
    assert data["sale"]["name"] == sale.name
    with pytest.raises(sale._meta.model.DoesNotExist):
        sale.refresh_from_db()


def test_sale_add_catalogues(
    staff_api_client, sale, category, product, collection, permission_manage_discounts
):
    query = """
        mutation saleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            saleCataloguesAdd(id: $id, input: $input) {
                discountErrors {
                    field
                    code
                    message
                }
            }
        }
    """
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesAdd"]

    assert not data["discountErrors"]
    assert product in sale.products.all()
    assert category in sale.categories.all()
    assert collection in sale.collections.all()


def test_sale_remove_catalogues(
    staff_api_client, sale, category, product, collection, permission_manage_discounts
):
    sale.products.add(product)
    sale.collections.add(collection)
    sale.categories.add(category)

    query = """
        mutation saleCataloguesRemove($id: ID!, $input: CatalogueInput!) {
            saleCataloguesRemove(id: $id, input: $input) {
                discountErrors {
                    field
                    code
                    message
                }
            }
        }
    """
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesRemove"]

    assert not data["discountErrors"]
    assert product not in sale.products.all()
    assert category not in sale.categories.all()
    assert collection not in sale.collections.all()


def test_sale_add_no_catalogues(staff_api_client, sale, permission_manage_discounts):
    query = """
        mutation saleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            saleCataloguesAdd(id: $id, input: $input) {
                discountErrors {
                    field
                    code
                    message
                }
            }
        }
    """
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {"products": [], "collections": [], "categories": []},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesAdd"]

    assert not data["discountErrors"]
    assert not sale.products.exists()
    assert not sale.categories.exists()
    assert not sale.collections.exists()


def test_sale_remove_no_catalogues(
    staff_api_client, sale, category, product, collection, permission_manage_discounts
):
    sale.products.add(product)
    sale.collections.add(collection)
    sale.categories.add(category)

    query = """
        mutation saleCataloguesAdd($id: ID!, $input: CatalogueInput!) {
            saleCataloguesAdd(id: $id, input: $input) {
                discountErrors {
                    field
                    code
                    message
                }
            }
        }
    """
    variables = {
        "id": graphene.Node.to_global_id("Sale", sale.id),
        "input": {"products": [], "collections": [], "categories": []},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["saleCataloguesAdd"]

    assert not data["discountErrors"]
    assert sale.products.exists()
    assert sale.categories.exists()
    assert sale.collections.exists()


@pytest.mark.parametrize(
    "voucher_filter, start_date, end_date, count",
    [
        (
            {"status": "ACTIVE"},
            timezone.now().replace(year=2015, month=1, day=1),
            timezone.now() + timedelta(days=365),
            2,
        ),
        (
            {"status": "EXPIRED"},
            timezone.now().replace(year=2015, month=1, day=1),
            timezone.now().replace(year=2018, month=1, day=1),
            1,
        ),
        (
            {"status": "SCHEDULED"},
            timezone.now() + timedelta(days=3),
            timezone.now() + timedelta(days=10),
            1,
        ),
    ],
)
def test_query_vouchers_with_filter_status(
    voucher_filter,
    start_date,
    end_date,
    count,
    staff_api_client,
    query_vouchers_with_filter,
    permission_manage_discounts,
):
    Voucher.objects.bulk_create(
        [
            Voucher(
                name="Voucher1",
                discount_value=123,
                code="abc",
                start_date=timezone.now(),
            ),
            Voucher(
                name="Voucher2",
                discount_value=123,
                code="123",
                start_date=start_date,
                end_date=end_date,
            ),
        ]
    )
    variables = {"filter": voucher_filter}
    response = staff_api_client.post_graphql(
        query_vouchers_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "voucher_filter, count",
    [
        ({"timesUsed": {"gte": 1, "lte": 5}}, 1),
        ({"timesUsed": {"lte": 3}}, 2),
        ({"timesUsed": {"gte": 2}}, 1),
    ],
)
def test_query_vouchers_with_filter_times_used(
    voucher_filter,
    count,
    staff_api_client,
    query_vouchers_with_filter,
    permission_manage_discounts,
):
    Voucher.objects.bulk_create(
        [
            Voucher(name="Voucher1", discount_value=123, code="abc"),
            Voucher(name="Voucher2", discount_value=123, code="123", used=2),
        ]
    )
    variables = {"filter": voucher_filter}
    response = staff_api_client.post_graphql(
        query_vouchers_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "voucher_filter, count",
    [
        ({"started": {"gte": "2019-04-18T00:00:00+00:00"}}, 1),
        ({"started": {"lte": "2012-01-14T00:00:00+00:00"}}, 1),
        (
            {
                "started": {
                    "lte": "2012-01-15T00:00:00+00:00",
                    "gte": "2012-01-01T00:00:00+00:00",
                }
            },
            1,
        ),
        ({"started": {"gte": "2012-01-03T00:00:00+00:00"}}, 2),
    ],
)
def test_query_vouchers_with_filter_started(
    voucher_filter,
    count,
    staff_api_client,
    query_vouchers_with_filter,
    permission_manage_discounts,
):
    Voucher.objects.bulk_create(
        [
            Voucher(name="Voucher1", discount_value=123, code="abc"),
            Voucher(
                name="Voucher2",
                discount_value=123,
                code="123",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
        ]
    )
    variables = {"filter": voucher_filter}
    response = staff_api_client.post_graphql(
        query_vouchers_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "voucher_filter, count, discount_value_type",
    [
        ({"discountType": "PERCENTAGE"}, 1, DiscountValueType.PERCENTAGE),
        ({"discountType": "FIXED"}, 2, DiscountValueType.FIXED),
    ],
)
def test_query_vouchers_with_filter_discount_type(
    voucher_filter,
    count,
    discount_value_type,
    staff_api_client,
    query_vouchers_with_filter,
    permission_manage_discounts,
):
    Voucher.objects.bulk_create(
        [
            Voucher(
                name="Voucher1",
                discount_value=123,
                code="abc",
                discount_value_type=DiscountValueType.FIXED,
            ),
            Voucher(
                name="Voucher2",
                discount_value=123,
                code="123",
                discount_value_type=discount_value_type,
            ),
        ]
    )
    variables = {"filter": voucher_filter}
    response = staff_api_client.post_graphql(
        query_vouchers_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "voucher_filter, count", [({"search": "Big"}, 1), ({"search": "GIFT"}, 2)]
)
def test_query_vouchers_with_filter_search(
    voucher_filter,
    count,
    staff_api_client,
    query_vouchers_with_filter,
    permission_manage_discounts,
):
    Voucher.objects.bulk_create(
        [
            Voucher(name="The Biggest Voucher", discount_value=123, code="GIFT"),
            Voucher(name="Voucher2", discount_value=123, code="GIFT-COUPON"),
        ]
    )
    variables = {"filter": voucher_filter}
    response = staff_api_client.post_graphql(
        query_vouchers_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"]
    assert len(data) == count


QUERY_VOUCHER_WITH_SORT = """
    query ($sort_by: VoucherSortingInput!) {
        vouchers(first:5, sortBy: $sort_by) {
            edges{
                node{
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "voucher_sort, result_order",
    [
        (
            {"field": "CODE", "direction": "ASC"},
            ["Voucher2", "Voucher1", "FreeShipping"],
        ),
        (
            {"field": "CODE", "direction": "DESC"},
            ["FreeShipping", "Voucher1", "Voucher2"],
        ),
        (
            {"field": "VALUE", "direction": "ASC"},
            ["Voucher2", "FreeShipping", "Voucher1"],
        ),
        (
            {"field": "VALUE", "direction": "DESC"},
            ["Voucher1", "FreeShipping", "Voucher2"],
        ),
        (
            {"field": "TYPE", "direction": "ASC"},
            ["Voucher1", "Voucher2", "FreeShipping"],
        ),
        (
            {"field": "TYPE", "direction": "DESC"},
            ["FreeShipping", "Voucher2", "Voucher1"],
        ),
        (
            {"field": "START_DATE", "direction": "ASC"},
            ["FreeShipping", "Voucher2", "Voucher1"],
        ),
        (
            {"field": "START_DATE", "direction": "DESC"},
            ["Voucher1", "Voucher2", "FreeShipping"],
        ),
        (
            {"field": "END_DATE", "direction": "ASC"},
            ["Voucher2", "FreeShipping", "Voucher1"],
        ),
        (
            {"field": "END_DATE", "direction": "DESC"},
            ["Voucher1", "FreeShipping", "Voucher2"],
        ),
        (
            {"field": "USAGE_LIMIT", "direction": "ASC"},
            ["Voucher1", "FreeShipping", "Voucher2"],
        ),
        (
            {"field": "USAGE_LIMIT", "direction": "DESC"},
            ["Voucher2", "FreeShipping", "Voucher1"],
        ),
        (
            {"field": "MINIMUM_SPENT_AMOUNT", "direction": "ASC"},
            ["Voucher2", "FreeShipping", "Voucher1"],
        ),
        (
            {"field": "MINIMUM_SPENT_AMOUNT", "direction": "DESC"},
            ["Voucher1", "FreeShipping", "Voucher2"],
        ),
    ],
)
def test_query_vouchers_with_sort(
    voucher_sort, result_order, staff_api_client, permission_manage_discounts
):
    Voucher.objects.bulk_create(
        [
            Voucher(
                name="Voucher1",
                discount_value=123,
                code="abc",
                discount_value_type=DiscountValueType.FIXED,
                type=VoucherType.ENTIRE_ORDER,
                usage_limit=10,
            ),
            Voucher(
                name="Voucher2",
                discount_value=23,
                code="123",
                discount_value_type=DiscountValueType.FIXED,
                type=VoucherType.ENTIRE_ORDER,
                start_date=timezone.now().replace(year=2012, month=1, day=5),
                end_date=timezone.now().replace(year=2013, month=1, day=5),
                min_spent_amount=50,
            ),
            Voucher(
                name="FreeShipping",
                discount_value=100,
                code="xyz",
                discount_value_type=DiscountValueType.PERCENTAGE,
                type=VoucherType.SHIPPING,
                start_date=timezone.now().replace(year=2011, month=1, day=5),
                end_date=timezone.now().replace(year=2015, month=12, day=31),
                usage_limit=1000,
                min_spent_amount=500,
            ),
        ]
    )
    variables = {"sort_by": voucher_sort}
    staff_api_client.user.user_permissions.add(permission_manage_discounts)
    response = staff_api_client.post_graphql(QUERY_VOUCHER_WITH_SORT, variables)
    content = get_graphql_content(response)
    vouchers = content["data"]["vouchers"]["edges"]

    for order, voucher_name in enumerate(result_order):
        assert vouchers[order]["node"]["name"] == voucher_name


@pytest.mark.parametrize(
    "sale_filter, start_date, end_date, count",
    [
        (
            {"status": "ACTIVE"},
            timezone.now().replace(year=2015, month=1, day=1),
            timezone.now() + timedelta(days=365),
            2,
        ),
        (
            {"status": "EXPIRED"},
            timezone.now().replace(year=2015, month=1, day=1),
            timezone.now().replace(year=2018, month=1, day=1),
            1,
        ),
        (
            {"status": "SCHEDULED"},
            timezone.now() + timedelta(days=3),
            timezone.now() + timedelta(days=10),
            1,
        ),
    ],
)
def test_query_sales_with_filter_status(
    sale_filter,
    start_date,
    end_date,
    count,
    staff_api_client,
    query_sales_with_filter,
    permission_manage_discounts,
):
    Sale.objects.bulk_create(
        [
            Sale(name="Sale1", value=123, start_date=timezone.now()),
            Sale(name="Sale2", value=123, start_date=start_date, end_date=end_date),
        ]
    )
    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        query_sales_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "sale_filter, count, sale_type",
    [
        ({"saleType": "PERCENTAGE"}, 1, DiscountValueType.PERCENTAGE),
        ({"saleType": "FIXED"}, 2, DiscountValueType.FIXED),
    ],
)
def test_query_sales_with_filter_discount_type(
    sale_filter,
    count,
    sale_type,
    staff_api_client,
    query_sales_with_filter,
    permission_manage_discounts,
):
    Sale.objects.bulk_create(
        [
            Sale(name="Sale1", value=123, type=DiscountValueType.FIXED),
            Sale(name="Sale2", value=123, type=sale_type),
        ]
    )
    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        query_sales_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "sale_filter, count",
    [
        ({"started": {"gte": "2019-04-18T00:00:00+00:00"}}, 1),
        ({"started": {"lte": "2012-01-14T00:00:00+00:00"}}, 1),
        (
            {
                "started": {
                    "lte": "2012-01-15T00:00:00+00:00",
                    "gte": "2012-01-01T00:00:00+00:00",
                }
            },
            1,
        ),
        ({"started": {"gte": "2012-01-03T00:00:00+00:00"}}, 2),
    ],
)
def test_query_sales_with_filter_started(
    sale_filter,
    count,
    staff_api_client,
    query_sales_with_filter,
    permission_manage_discounts,
):
    Sale.objects.bulk_create(
        [
            Sale(name="Sale1", value=123),
            Sale(
                name="Sale2",
                value=123,
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
        ]
    )
    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        query_sales_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


@pytest.mark.parametrize(
    "sale_filter, count",
    [({"search": "Big"}, 1), ({"search": "69"}, 1), ({"search": "FIX"}, 2)],
)
def test_query_sales_with_filter_search(
    sale_filter,
    count,
    staff_api_client,
    query_sales_with_filter,
    permission_manage_discounts,
):
    Sale.objects.bulk_create(
        [
            Sale(name="BigSale", value=123, type="PERCENTAGE"),
            Sale(
                name="Sale2",
                value=123,
                type="FIXED",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
            Sale(
                name="Sale3",
                value=69,
                type="FIXED",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
            ),
        ]
    )
    variables = {"filter": sale_filter}
    response = staff_api_client.post_graphql(
        query_sales_with_filter, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["sales"]["edges"]
    assert len(data) == count


QUERY_SALE_WITH_SORT = """
    query ($sort_by: SaleSortingInput!) {
        sales(first:5, sortBy: $sort_by) {
            edges{
                node{
                    name
                }
            }
        }
    }
"""


@pytest.mark.parametrize(
    "sale_sort, result_order",
    [
        ({"field": "NAME", "direction": "ASC"}, ["BigSale", "Sale2", "Sale3"]),
        ({"field": "NAME", "direction": "DESC"}, ["Sale3", "Sale2", "BigSale"]),
        ({"field": "VALUE", "direction": "ASC"}, ["Sale3", "Sale2", "BigSale"]),
        ({"field": "VALUE", "direction": "DESC"}, ["BigSale", "Sale2", "Sale3"]),
        ({"field": "TYPE", "direction": "ASC"}, ["Sale2", "Sale3", "BigSale"]),
        ({"field": "TYPE", "direction": "DESC"}, ["BigSale", "Sale3", "Sale2"]),
        ({"field": "START_DATE", "direction": "ASC"}, ["Sale3", "Sale2", "BigSale"]),
        ({"field": "START_DATE", "direction": "DESC"}, ["BigSale", "Sale2", "Sale3"]),
        ({"field": "END_DATE", "direction": "ASC"}, ["Sale2", "Sale3", "BigSale"]),
        ({"field": "END_DATE", "direction": "DESC"}, ["BigSale", "Sale3", "Sale2"]),
    ],
)
def test_query_sales_with_sort(
    sale_sort, result_order, staff_api_client, permission_manage_discounts
):
    Sale.objects.bulk_create(
        [
            Sale(name="BigSale", value=1234, type="PERCENTAGE"),
            Sale(
                name="Sale2",
                value=123,
                type="FIXED",
                start_date=timezone.now().replace(year=2012, month=1, day=5),
                end_date=timezone.now().replace(year=2013, month=1, day=5),
            ),
            Sale(
                name="Sale3",
                value=69,
                type="FIXED",
                start_date=timezone.now().replace(year=2011, month=1, day=5),
                end_date=timezone.now().replace(year=2015, month=12, day=31),
            ),
        ]
    )
    variables = {"sort_by": sale_sort}
    staff_api_client.user.user_permissions.add(permission_manage_discounts)
    response = staff_api_client.post_graphql(QUERY_SALE_WITH_SORT, variables)
    content = get_graphql_content(response)
    sales = content["data"]["sales"]["edges"]

    for order, sale_name in enumerate(result_order):
        assert sales[order]["node"]["name"] == sale_name
