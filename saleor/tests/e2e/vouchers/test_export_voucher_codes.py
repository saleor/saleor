import uuid

import pytest

from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    create_voucher,
    create_voucher_channel_listing,
    export_voucher_codes,
    raw_export_voucher_codes,
)


def create_vouchers_with_multiple_codes(e2e_staff_api_client, channel_id):
    voucher_ids = []
    voucher_code_ids = []

    for i in range(5):
        voucher_code = f"voucher_code_{i + 1}_{uuid.uuid4()}"

        input_data = {
            "addCodes": [voucher_code],
            "discountValueType": "PERCENTAGE",
            "type": "ENTIRE_ORDER",
        }
        voucher_data = create_voucher(e2e_staff_api_client, input_data)

        voucher_id = voucher_data["id"]
        for i in range(len(voucher_data["codes"]["edges"])):
            voucher_code_id = voucher_data["codes"]["edges"][i]["node"]["id"]
            voucher_code_ids.append(voucher_code_id)

        channel_listing = [
            {
                "channelId": channel_id,
                "discountValue": i + 1,
            },
        ]
        create_voucher_channel_listing(
            e2e_staff_api_client,
            voucher_id,
            channel_listing,
        )

        voucher_ids.append(voucher_id)

    return voucher_ids, voucher_code_ids


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("file_type", "voucher_id_array_index"),
    [
        ("CSV", 0),
        ("XLSX", 2),
    ],
)
def test_export_valid_voucher_ids_CORE_0925(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_discounts,
    permission_manage_checkouts,
    file_type,
    voucher_id_array_index,
    media_root,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_discounts,
        permission_manage_checkouts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]

    voucher_ids, _voucher_code_ids = create_vouchers_with_multiple_codes(
        e2e_staff_api_client, channel_id
    )

    voucher_id_array_index = [voucher_ids[voucher_id_array_index]]

    # Step 1 - Export voucher codes and check status
    input_data = {
        "fileType": file_type,
        "voucherId": voucher_id_array_index,
    }
    response = export_voucher_codes(e2e_staff_api_client, input_data)

    assert response["status"] == "SUCCESS"


@pytest.mark.e2e
@pytest.mark.parametrize(
    (
        "file_type",
        "voucher_code_id_indexes",
        "voucher_id_array_index",
    ),
    [
        (
            "XLSX",
            [3, 5],
            1,
        ),
        (
            "CSV",
            [0, 2],
            2,
        ),
    ],
)
def test_export_voucher_ids_and_codes_CORE_0925(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_discounts,
    permission_manage_checkouts,
    file_type,
    voucher_code_id_indexes,
    voucher_id_array_index,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_discounts,
        permission_manage_checkouts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]

    voucher_ids, voucher_code_ids = create_vouchers_with_multiple_codes(
        e2e_staff_api_client, channel_id
    )

    voucher_id_array_index = [voucher_ids[voucher_id_array_index]]

    voucher_code_id_indexes = [
        index for index in voucher_code_id_indexes if index < len(voucher_code_ids)
    ]

    # Step 1 - Export voucher codes and check status
    input = {
        "fileType": file_type,
        "ids": [voucher_code_ids[i] for i in voucher_code_id_indexes],
        "voucherId": voucher_id_array_index,
    }
    response = raw_export_voucher_codes(e2e_staff_api_client, input)
    error = response["data"]["exportVoucherCodes"]["errors"][0]
    assert error["message"] == "Argument 'voucher_id' cannot be combined with 'ids'"
    assert error["code"] == "GRAPHQL_ERROR"


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("file_type", "voucher_code_id_indexes"),
    [
        ("CSV", [0]),
        ("XLSX", [0, 1, 2, 3, 4, 5]),
    ],
)
def test_export_valid_voucher_code_ids_CORE_0925(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_discounts,
    permission_manage_checkouts,
    file_type,
    voucher_code_id_indexes,
    media_root,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_discounts,
        permission_manage_checkouts,
    ]

    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]

    _voucher_ids, voucher_code_ids = create_vouchers_with_multiple_codes(
        e2e_staff_api_client, channel_id
    )

    voucher_code_id_indexes = [
        index for index in voucher_code_id_indexes if index < len(voucher_code_ids)
    ]

    # Step 1 - Export voucher codes and check status
    input_data = {
        "fileType": file_type,
        "ids": [voucher_code_ids[i] for i in voucher_code_id_indexes],
    }
    response = export_voucher_codes(e2e_staff_api_client, input_data)

    assert response["status"] == "SUCCESS"


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("file_type"),
    [
        ("XLSX"),
        ("CSV"),
    ],
)
def test_export_voucher_codes_with_invalid_voucher_id_CORE_0925(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_discounts,
    permission_manage_checkouts,
    file_type,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_discounts,
        permission_manage_checkouts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    # Step 1 - Export voucher codes and check status
    input_data = {
        "fileType": file_type,
        "voucherId": "invalid_voucher_id",
    }
    response = raw_export_voucher_codes(e2e_staff_api_client, input_data)

    error = response["data"]["exportVoucherCodes"]["errors"][0]
    assert error["message"] == "Invalid voucher ID."
    assert error["code"] == "INVALID"
    assert error["field"] == "voucherId"


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("file_type"),
    [
        ("XLSX"),
        ("CSV"),
    ],
)
def test_export_voucher_codes_with_invalid_voucher_codes_CORE_0925(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_discounts,
    permission_manage_checkouts,
    file_type,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_discounts,
        permission_manage_checkouts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    # Step 1 - Export voucher codes and check status
    input_data = {
        "fileType": file_type,
        "ids": ["invalid_voucher_code"],
    }
    response = raw_export_voucher_codes(e2e_staff_api_client, input_data)
    error = response["data"]["exportVoucherCodes"]["errors"][0]
    assert error["message"] == "Invalid voucher code IDs."
    assert error["code"] == "INVALID"
    assert error["field"] == "ids"


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("file_type"),
    [
        ("XLSX"),
        ("CSV"),
    ],
)
def test_export_voucher_codes_without_voucher_id_nor_codes_CORE_0925(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_discounts,
    permission_manage_checkouts,
    file_type,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_discounts,
        permission_manage_checkouts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    # Step 1 - Export voucher codes and check status
    input_data = {
        "fileType": file_type,
    }
    response = raw_export_voucher_codes(e2e_staff_api_client, input_data)
    error = response["data"]["exportVoucherCodes"]["errors"][0]
    assert (
        error["message"]
        == "At least one of arguments is required: 'voucher_id', 'ids'."
    )
    assert error["code"] == "GRAPHQL_ERROR"


@pytest.mark.e2e
@pytest.mark.parametrize(
    ("file_type", "voucher_id"),
    [
        (
            "",
            "{voucher_id}",
        ),
        (
            "SVG",
            "{voucher_id}",
        ),
    ],
)
def test_export_voucher_codes_with_invalid_file_type_CORE_0925(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_discounts,
    permission_manage_checkouts,
    file_type,
    voucher_id,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_discounts,
        permission_manage_checkouts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]

    voucher_ids, _voucher_code_ids = create_vouchers_with_multiple_codes(
        e2e_staff_api_client, channel_id
    )

    voucher_id = voucher_ids[0]

    # Step 1 - Export voucher codes and check status
    input_data = {
        "fileType": file_type,
        "voucherId": voucher_id,
    }

    response = raw_export_voucher_codes(e2e_staff_api_client, input_data)

    response_errors = response.get("errors")

    expected_error_message = f'Variable "$input" got invalid value {{"fileType": "{file_type}", "voucherId": "{voucher_id}"}}.\nIn field "fileType": Expected type "FileTypesEnum", found "{file_type}".'

    expected_error = {
        "extensions": {"exception": {"code": "GraphQLError"}},
        "locations": [{"column": 24, "line": 2}],
        "message": expected_error_message,
    }

    expected_errors_list = [expected_error]

    assert response_errors == expected_errors_list
