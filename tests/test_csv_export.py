import shutil
import tempfile
from unittest.mock import ANY, MagicMock, patch

import pytest
from django.core.files import File
from django.test import override_settings

from saleor.csv import JobStatus
from saleor.csv.models import Job
from saleor.csv.utils.export import (
    export_products,
    get_product_queryset,
    prepare_products_data,
    prepare_warehouse_data,
    update_job,
)
from saleor.product.models import Product


@pytest.mark.parametrize("scope", [{"filter": {"is_published": True}}, {"all": ""}])
@patch("saleor.csv.utils.export.update_job")
def test_export_products(update_job_mock, product_list, job, scope):
    export_products(scope, job.id)

    job.refresh_from_db()
    update_job_mock.called_once_with(job.id, ANY)


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
@patch("saleor.csv.utils.export.update_job")
def test_export_products_ids(update_job_mock, product_list, job):
    pks = [product.pk for product in product_list[:2]]

    assert job.status == JobStatus.PENDING
    assert not job.ended_at
    assert not job.content_file

    export_products({"ids": pks}, job.id)

    job.refresh_from_db()
    update_job_mock.called_once_with(job.id, ANY)


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
def test_update_job(job):
    file_mock = MagicMock(spec=File)
    file_mock.name = "temp_file.csv"
    file_name = "test.csv"

    assert job.status == JobStatus.PENDING
    assert not job.ended_at
    assert not job.content_file

    update_job(job.pk, file_mock, file_name)

    job.refresh_from_db()
    assert job.status.split(".")[1] == JobStatus.SUCCESS.name
    assert job.ended_at
    assert job.content_file

    job_csv_upload_dir = Job.content_file.field.upload_to
    csv_upload_dir = f"{tempfile.gettempdir()}/{job_csv_upload_dir}"
    shutil.rmtree(csv_upload_dir)


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


def test_prepare_products_data(product, product_with_image, collection):
    headers_mapping = {
        "product": {"id": "id", "name": "name"},
        "variant": {"sku": "sku"},
    }
    collection.products.add(product)

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
            "" if not product.images.all() else product.images.first().image.url
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
                "" if not variant.images.all() else variant.images.first().image.url
            )
            variant_data["sku"] = variant.sku

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


def test_prepare_warehouse_data(product):
    variant = product.variants.first()
    result = prepare_warehouse_data(variant)

    expected_result = {}
    for stock in variant.stock.all():
        slug = stock.warehouse.slug
        expected_result[
            f"{slug} (warehouse quantity allocated)"
        ] = stock.quantity_allocated
        expected_result[f"{slug} (warehouse quantity)"] = stock.quantity

    assert result == expected_result
