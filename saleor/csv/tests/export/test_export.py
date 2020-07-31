import shutil
from unittest.mock import MagicMock, patch

from django.core.files import File
from freezegun import freeze_time

from ....core import JobStatus
from ....graphql.csv.enums import ProductFieldEnum
from ... import FileTypes
from ...utils.export import (
    export_products,
    get_filename,
    get_product_queryset,
    save_csv_file_in_export_file,
)


@patch("saleor.csv.utils.export.save_csv_file_in_export_file")
@patch("saleor.csv.utils.export.send_email_with_link_to_download_file")
def test_export_products_ids(
    send_email_mock, save_csv_file_mock, product_list, user_export_file,
):
    # given
    pks = [product.pk for product in product_list[:2]]
    export_info = {"fields": [], "warehouses": [], "attributes": []}
    file_type = FileTypes.CSV

    assert user_export_file.status == JobStatus.PENDING
    assert not user_export_file.content_file

    # when
    export_products(user_export_file, {"ids": pks}, export_info, file_type)

    # then
    assert save_csv_file_mock.call_args[0][0] == user_export_file
    assert save_csv_file_mock.call_args[0][2].startswith("product_data_")
    send_email_mock.assert_called_once_with(
        user_export_file, user_export_file.user.email, "export_products_success"
    )


@patch("saleor.csv.utils.export.save_csv_file_in_export_file")
@patch("saleor.csv.utils.export.send_email_with_link_to_download_file")
def test_export_products_filter(
    send_email_mock, save_csv_file_mock, product_list, user_export_file,
):
    # given
    product_list[0].is_published = False
    product_list[0].save(update_fields=["is_published"])

    export_info = {"fields": [], "warehouses": [], "attributes": []}
    file_type = FileTypes.CSV

    assert user_export_file.status == JobStatus.PENDING
    assert not user_export_file.content_file

    # when
    export_products(
        user_export_file, {"filter": {"is_published": True}}, export_info, file_type
    )

    # then
    assert save_csv_file_mock.called
    send_email_mock.called_once_with(
        user_export_file, user_export_file.user.email, "export_products_success"
    )


@patch("saleor.csv.utils.export.save_csv_file_in_export_file")
@patch("saleor.csv.utils.export.send_email_with_link_to_download_file")
def test_export_products_by_app(
    send_email_mock, save_csv_file_mock, product_list, app_export_file,
):
    # given
    export_info = {
        "fields": [ProductFieldEnum.NAME.value],
        "warehouses": [],
        "attributes": [],
    }
    file_type = FileTypes.CSV

    # when
    export_products(app_export_file, {"all": ""}, export_info, file_type)

    # then
    assert save_csv_file_mock.called
    send_email_mock.assert_not_called()


def test_get_filename_csv():
    with freeze_time("2000-02-09"):
        file_name = get_filename("test", FileTypes.CSV)

        assert file_name == "test_data_09_02_2000.csv"


def test_get_filename_xlsx():
    with freeze_time("2000-02-09"):
        file_name = get_filename("test", FileTypes.XLSX)

        assert file_name == "test_data_09_02_2000.xlsx"


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


def test_save_csv_file_in_export_file(user_export_file, tmpdir, media_root):
    file_mock = MagicMock(spec=File)
    file_mock.name = "temp_file.csv"
    file_name = "test.csv"

    assert not user_export_file.content_file

    save_csv_file_in_export_file(user_export_file, file_mock, file_name)

    user_export_file.refresh_from_db()
    assert user_export_file.content_file

    shutil.rmtree(tmpdir)
