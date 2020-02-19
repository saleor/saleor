import datetime
import tempfile
from unittest.mock import ANY, MagicMock, patch

import pytest
import pytz
from django.core.files import File
from django.test import override_settings
from freezegun import freeze_time

from saleor.csv import JobStatus
from saleor.csv.models import Job
from saleor.csv.utils.export import (
    add_attribute_info_to_data,
    add_collection_info_to_data,
    add_image_uris_to_data,
    add_warehouse_info_to_data,
    create_csv_file_and_save_in_job,
    export_products,
    get_filename,
    get_product_queryset,
    on_task_failure,
    on_task_success,
    prepare_product_relations_data,
    prepare_products_data,
    prepare_variants_data,
    save_csv_file_in_job,
    update_job_when_task_finished,
)
from saleor.product.models import Product, VariantImage
from tests.utils import clear_temporary_dir


def test_on_task_failure(job):
    exc = Exception("Test")
    task_id = "task_id"
    args = [job.pk, {"all": ""}]
    kwargs = {}
    einfo = None

    assert job.status == JobStatus.PENDING
    assert job.created_at
    assert not job.completed_at

    on_task_failure(None, exc, task_id, args, kwargs, einfo)

    job.refresh_from_db()
    assert job.status == JobStatus.FAILED
    assert job.created_at
    assert job.completed_at


def test_on_task_success(job):
    task_id = "task_id"
    args = [job.pk, {"filter": {}}]
    kwargs = {}

    assert job.status == JobStatus.PENDING
    assert job.created_at
    assert not job.completed_at

    on_task_success(None, None, task_id, args, kwargs)

    job.refresh_from_db()
    assert job.status == JobStatus.SUCCESS
    assert job.created_at
    assert job.completed_at


def test_update_job_when_task_finished(job):
    with freeze_time(datetime.datetime.now()) as frozen_datetime:
        assert not job.completed_at
        update_job_when_task_finished(job.pk, JobStatus.FAILED)

        job.refresh_from_db()
        assert job.completed_at == pytz.utc.localize(frozen_datetime())


@pytest.mark.parametrize("scope", [{"filter": {"is_published": True}}, {"all": ""}])
@patch("saleor.csv.utils.export.send_email_with_link_to_download_csv")
@patch("saleor.csv.utils.export.save_csv_file_in_job")
def test_export_products(
    save_csv_file_in_job_mock, send_email_mock, product_list, job, scope
):
    export_products(job.id, scope)

    save_csv_file_in_job_mock.called_once_with(job, ANY)
    send_email_mock.called_once_with(job)


@patch("saleor.csv.utils.export.send_email_with_link_to_download_csv")
@patch("saleor.csv.utils.export.save_csv_file_in_job")
def test_export_products_ids(
    save_csv_file_in_job_mock, send_email_mock, product_list, job
):
    pks = [product.pk for product in product_list[:2]]

    assert job.status == JobStatus.PENDING
    assert not job.completed_at
    assert not job.content_file

    export_products(job.id, {"ids": pks})

    save_csv_file_in_job_mock.called_once_with(job, ANY)
    send_email_mock.called_once_with(job)


def test_get_filename():
    with freeze_time("2000-02-09"):
        file_name = get_filename("test")

        assert file_name == "test_data_09_02_2000.csv"


def test_get_product_queryset_all(product_list):
    queryset = get_product_queryset({"all": ""})

    assert queryset.count() == len(product_list)


def test_get_product_queryset_ids(product_list):
    pks = [product.pk for product in product_list[:2]]
    queryset = get_product_queryset({"ids": pks})

    assert queryset.count() == len(pks)


def get_product_queryset_filter(product_list):
    product_not_published = product_list.first()
    product_not_published.is_published = False
    product_not_published.save()

    queryset = get_product_queryset({"ids": {"is_published": True}})

    assert queryset.count() == len(product_list) - 1


def test_prepare_products_data(product, product_with_image, collection, image):
    headers_mapping = {
        "product": {"id": "id", "name": "name"},
        "variant": {"sku": "sku"},
    }
    collection.products.add(product)

    variant = product.variants.first()
    VariantImage.objects.create(variant=variant, image=product.images.first())

    products = Product.objects.all()
    data, headers = prepare_products_data(products, headers_mapping)

    expected_data = []
    expected_headers = set()
    for product in products.order_by("pk"):
        product_data = {}
        product_data["collections"] = (
            "" if not product.collections.all() else product.collections.first().slug
        )
        product_data["name"] = product.name
        product_data["id"] = product.pk
        product_data["images"] = (
            ""
            if not product.images.all()
            else "http://mirumee.com{}".format(product.images.first().image.url)
        )

        assigned_attribute = product.attributes.first()
        if assigned_attribute:
            header = f"{assigned_attribute.attribute.slug} (attribute)"
            product_data[header] = assigned_attribute.values.first().slug
            expected_headers.add(header)

        expected_data.append(product_data)

        for variant in product.variants.all():
            variant_data = {}
            variant_data["images"] = (
                ""
                if not variant.images.all()
                else "http://mirumee.com{}".format(variant.images.first().image.url)
            )
            variant_data["sku"] = variant.sku
            variant_data["variant_currency"] = variant.currency
            variant_data["price_override_amount"] = variant.price_override_amount
            variant_data["cost_price_amount"] = variant.cost_price_amount

            for stock in variant.stock.all():
                slug = stock.warehouse.slug
                warehouse_headers = [
                    f"{slug} (warehouse quantity allocated)",
                    f"{slug} (warehouse quantity)",
                ]
                variant_data[warehouse_headers[0]] = stock.quantity_allocated
                variant_data[warehouse_headers[1]] = stock.quantity
                expected_headers.update(warehouse_headers)

            assigned_attribute = variant.attributes.first()
            if assigned_attribute:
                header = f"{assigned_attribute.attribute.slug} (attribute)"
                variant_data[header] = assigned_attribute.values.first().slug
                expected_headers.add(header)

            expected_data.append(variant_data)

    assert data == expected_data
    assert set(headers) == expected_headers


def test_prepare_product_relations_data(product_with_image, collection_list):
    pk = product_with_image.pk
    collection_list[0].products.add(product_with_image)
    collection_list[1].products.add(product_with_image)
    qs = Product.objects.all()
    result, result_headers = prepare_product_relations_data(qs)

    collections = ", ".join(
        sorted([collection.slug for collection in collection_list[:2]])
    )
    images = ", ".join(
        [
            "http://mirumee.com/media/" + image.image.name
            for image in product_with_image.images.all()
        ]
    )
    expected_result = {pk: {"collections": collections, "images": images}}

    assigned_attribute = product_with_image.attributes.first()
    if assigned_attribute:
        header = f"{assigned_attribute.attribute.slug} (attribute)"
        expected_result[pk][header] = assigned_attribute.values.first().slug

    assert result == expected_result


def test_prepare_variants_data(product):
    variant = product.variants.first()

    warehouse_headers = set()
    attribute_headers = set()

    expected_result = {
        "sku": variant.sku,
        "cost_price_amount": variant.cost_price_amount,
        "price_override_amount": variant.price_override_amount,
        "variant_currency": variant.currency,
    }
    assigned_attribute = variant.attributes.first()
    if assigned_attribute:
        header = f"{assigned_attribute.attribute.slug} (attribute)"
        expected_result[header] = assigned_attribute.values.first().slug
        attribute_headers.add(header)

    stock = variant.stock
    for stock in variant.stock.all():
        slug = stock.warehouse.slug
        headers = [
            f"{slug} (warehouse quantity allocated)",
            f"{slug} (warehouse quantity)",
        ]
        expected_result[headers[0]] = stock.quantity_allocated
        expected_result[headers[1]] = stock.quantity
        warehouse_headers.update(headers)

    result_data, res_attribute_headers, res_warehouse_headers = prepare_variants_data(
        product.pk
    )

    assert result_data == [expected_result]
    assert res_attribute_headers == attribute_headers
    assert res_warehouse_headers == warehouse_headers


def test_add_collection_info_to_data(product):
    pk = product.pk
    collection = "test_collection"
    input_data = {pk: {}}
    result = add_collection_info_to_data(product.pk, collection, input_data)

    assert result[pk]["collections"] == {collection}


def test_add_collection_info_to_data_update_collections(product):
    pk = product.pk
    existing_collection = "test2"
    collection = "test_collection"
    input_data = {pk: {"collections": {existing_collection}}}
    result = add_collection_info_to_data(product.pk, collection, input_data)

    assert result[pk]["collections"] == {collection, existing_collection}


def test_add_collection_info_to_data_no_collection(product):
    pk = product.pk
    collection = None
    input_data = {pk: {}}
    result = add_collection_info_to_data(product.pk, collection, input_data)

    assert result == input_data


def test_add_image_uris_to_data(product):
    pk = product.pk
    image_path = "test/path/image.jpg"
    input_data = {pk: {}}
    result = add_image_uris_to_data(product.pk, image_path, input_data)

    assert result[pk]["images"] == {"http://mirumee.com/media/" + image_path}


def test_add_image_uris_to_data_update_images(product):
    pk = product.pk
    old_path = "http://mirumee.com/media/test/image0.jpg"
    image_path = "test/path/image.jpg"
    input_data = {pk: {"images": {old_path}}}
    result = add_image_uris_to_data(product.pk, image_path, input_data)

    assert result[pk]["images"] == {"http://mirumee.com/media/" + image_path, old_path}


def test_add_image_uris_to_data_no_image_path(product):
    pk = product.pk
    image_path = None
    input_data = {pk: {"name": "test"}}
    result = add_image_uris_to_data(product.pk, image_path, input_data)

    assert result == input_data


def test_add_attribute_info_to_data(product):
    pk = product.pk
    slug = "test_attribute_slug"
    value = "test value"
    attribute_data = {
        "slug": slug,
        "value": value,
    }
    input_data = {pk: {}}
    result, header = add_attribute_info_to_data(product.pk, attribute_data, input_data)

    expected_header = f"{slug} (attribute)"

    assert header == expected_header
    assert result[pk][header] == {value}


def test_add_attribute_info_to_data_update_attribute_data(product):
    pk = product.pk
    slug = "test_attribute_slug"
    value = "test value"
    expected_header = f"{slug} (attribute)"

    attribute_data = {
        "slug": slug,
        "value": value,
    }
    input_data = {pk: {expected_header: {"value1"}}}
    result, header = add_attribute_info_to_data(product.pk, attribute_data, input_data)

    assert header == expected_header
    assert result[pk][header] == {value, "value1"}


def test_add_attribute_info_to_data_no_slug(product):
    pk = product.pk
    attribute_data = {
        "slug": None,
        "value": None,
    }
    input_data = {pk: {}}
    result, header = add_attribute_info_to_data(product.pk, attribute_data, input_data)

    assert not header
    assert result == input_data


def test_add_warehouse_info_to_data(product):
    pk = product.pk
    slug = "test_warehouse"
    warehouse_data = {
        "slug": slug,
        "qty": 12,
        "qty_alc": 10,
    }
    input_data = {pk: {}}
    result, headers = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    expected_headers = [
        f"{slug} (warehouse quantity)",
        f"{slug} (warehouse quantity allocated)",
    ]
    assert result[pk][expected_headers[0]] == 12
    assert result[pk][expected_headers[1]] == 10
    assert headers == set(expected_headers)


def test_add_warehouse_info_to_data_data_not_changed(product):
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
    result, headers = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    assert result == input_data
    assert headers == set()


def test_add_warehouse_info_to_data_data_no_slug(product):
    pk = product.pk
    warehouse_data = {
        "slug": None,
        "qty": None,
        "qty_alc": None,
    }
    input_data = {pk: {}}
    result, headers = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    assert result == input_data
    assert headers == set()


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_create_csv_file_and_save_in_job(job):
    export_data = [
        {"id": "123", "name": "test1", "collections": "coll1"},
        {"id": "345", "name": "test2"},
    ]
    headers = ["id", "name", "collections"]
    csv_headers_mapping = {"id": "ID", "name": "NAME"}
    delimiter = ";"
    job = job
    file_name = "test.csv"

    job_csv_upload_dir = Job.content_file.field.upload_to

    assert not job.content_file

    create_csv_file_and_save_in_job(
        export_data, headers, csv_headers_mapping, delimiter, job, file_name
    )

    csv_file = job.content_file
    assert csv_file
    assert csv_file.name == f"{job_csv_upload_dir}/{file_name}"

    file_content = csv_file.read().decode().split("\r\n")
    headers = list(csv_headers_mapping.values())
    headers.append("collections")

    assert ";".join(headers) in file_content
    assert ";".join(export_data[0].values()) in file_content
    assert (";".join(export_data[1].values()) + "; ") in file_content

    clear_temporary_dir(job_csv_upload_dir)


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_save_csv_file_in_job(job):
    file_mock = MagicMock(spec=File)
    file_mock.name = "temp_file.csv"
    file_name = "test.csv"

    assert not job.content_file

    save_csv_file_in_job(job, file_mock, file_name)

    job.refresh_from_db()
    assert job.content_file

    job_csv_upload_dir = Job.content_file.field.upload_to
    clear_temporary_dir(job_csv_upload_dir)
