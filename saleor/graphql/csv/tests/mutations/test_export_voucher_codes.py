from unittest.mock import patch

import graphene

from .....csv import ExportEvents
from .....csv.error_codes import ExportErrorCode
from .....csv.models import ExportEvent
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import FileTypeEnum

EXPORT_VOUCHER_CODES_MUTATION = """
    mutation ExportVoucherCodes($input: ExportVoucherCodesInput!){
        exportVoucherCodes(input: $input){
            exportFile {
                id
                status
                createdAt
                updatedAt
                url
                user {
                    email
                }
                app {
                    name
                }
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


@patch(
    "saleor.graphql.csv.mutations.export_voucher_codes.export_voucher_codes_task.delay"
)
def test_export_voucher_codes_by_voucher_id(
    export_voucher_codes_mock,
    staff_api_client,
    voucher_with_many_codes,
    permission_manage_discounts,
):
    # given
    user = staff_api_client.user
    voucher_id = graphene.Node.to_global_id("Voucher", voucher_with_many_codes.id)
    variables = {
        "input": {
            "voucherId": voucher_id,
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        EXPORT_VOUCHER_CODES_MUTATION,
        variables=variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["exportVoucherCodes"]
    export_file_data = data["exportFile"]

    assert not data["errors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"]["email"] == staff_api_client.user.email
    assert export_file_data["app"] is None
    assert ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
    ).exists()

    export_voucher_codes_mock.assert_called_once()


@patch(
    "saleor.graphql.csv.mutations.export_voucher_codes.export_voucher_codes_task.delay"
)
def test_export_voucher_codes_by_voucher_code_ids(
    export_voucher_codes_mock,
    staff_api_client,
    voucher_with_many_codes,
    permission_manage_discounts,
):
    # given
    user = staff_api_client.user
    code_ids = [
        graphene.Node.to_global_id("VoucherCode", code.id)
        for code in voucher_with_many_codes.codes.all()
    ]
    variables = {
        "input": {
            "ids": code_ids,
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        EXPORT_VOUCHER_CODES_MUTATION,
        variables=variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["exportVoucherCodes"]
    export_file_data = data["exportFile"]

    assert not data["errors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"]["email"] == staff_api_client.user.email
    assert export_file_data["app"] is None
    assert ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
    ).exists()

    export_voucher_codes_mock.assert_called_once()


@patch(
    "saleor.graphql.csv.mutations.export_voucher_codes.export_voucher_codes_task.delay"
)
def test_export_voucher_codes_by_app(
    export_voucher_codes_mock,
    app_api_client,
    voucher_with_many_codes,
    permission_manage_discounts,
    permission_manage_apps,
):
    # given
    query = """
    mutation ExportVoucherCodes($input: ExportVoucherCodesInput!){
        exportVoucherCodes(input: $input){
            exportFile {
                id
                status
                createdAt
                updatedAt
                url
                app {
                    name
                }
            }
            errors {
                field
                code
                message
            }
        }
    }
    """
    app = app_api_client.app
    voucher_id = graphene.Node.to_global_id("Voucher", voucher_with_many_codes.id)
    variables = {
        "input": {
            "voucherId": voucher_id,
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_discounts, permission_manage_apps],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["exportVoucherCodes"]
    export_file_data = data["exportFile"]

    assert not data["errors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["app"]["name"] == app.name
    assert ExportEvent.objects.filter(
        user=None, app=app, type=ExportEvents.EXPORT_PENDING
    ).exists()

    export_voucher_codes_mock.assert_called_once()


def test_export_voucher_codes_by_staff_no_permission(
    staff_api_client,
    voucher_with_many_codes,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher_with_many_codes.id)
    variables = {
        "input": {
            "voucherId": voucher_id,
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        EXPORT_VOUCHER_CODES_MUTATION,
        variables=variables,
    )

    # then
    assert_no_permission(response)


def test_export_voucher_codes_by_app_no_permission(
    app_api_client,
    voucher_with_many_codes,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher_with_many_codes.id)
    variables = {
        "input": {
            "voucherId": voucher_id,
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = app_api_client.post_graphql(
        EXPORT_VOUCHER_CODES_MUTATION,
        variables=variables,
    )

    # then
    assert_no_permission(response)


def test_export_voucher_codes_error_too_many_arguments(
    staff_api_client,
    voucher_with_many_codes,
    permission_manage_discounts,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher_with_many_codes.id)
    code_ids = [
        graphene.Node.to_global_id("VoucherCode", code.id)
        for code in voucher_with_many_codes.codes.all()
    ]
    variables = {
        "input": {
            "voucherId": voucher_id,
            "ids": code_ids,
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        EXPORT_VOUCHER_CODES_MUTATION,
        variables=variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["exportVoucherCodes"]

    assert not data["exportFile"]
    error = data["errors"][0]
    assert error["field"] is None
    assert error["code"] == ExportErrorCode.GRAPHQL_ERROR.name


def test_export_voucher_codes_error_lack_of_required_argument(
    staff_api_client,
    permission_manage_discounts,
):
    # given
    variables = {"input": {"fileType": FileTypeEnum.CSV.name}}

    # when
    response = staff_api_client.post_graphql(
        EXPORT_VOUCHER_CODES_MUTATION,
        variables=variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["exportVoucherCodes"]

    assert not data["exportFile"]
    error = data["errors"][0]
    assert error["field"] is None
    assert error["code"] == ExportErrorCode.GRAPHQL_ERROR.name


def test_export_voucher_codes_error_invalid_voucher_id(
    staff_api_client,
    voucher_with_many_codes,
    permission_manage_discounts,
):
    # given
    voucher_id = graphene.Node.to_global_id("Product", voucher_with_many_codes.id)
    variables = {
        "input": {
            "voucherId": voucher_id,
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        EXPORT_VOUCHER_CODES_MUTATION,
        variables=variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["exportVoucherCodes"]

    assert not data["exportFile"]
    error = data["errors"][0]
    assert error["field"] == "voucherId"
    assert error["code"] == ExportErrorCode.INVALID.name


def test_export_voucher_codes_error_invalid_voucher_code_ids(
    staff_api_client,
    voucher_with_many_codes,
    permission_manage_discounts,
):
    # given
    code_ids = [
        graphene.Node.to_global_id("Product", code.id)
        for code in voucher_with_many_codes.codes.all()
    ]
    variables = {
        "input": {
            "ids": code_ids,
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        EXPORT_VOUCHER_CODES_MUTATION,
        variables=variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["exportVoucherCodes"]

    assert not data["exportFile"]
    error = data["errors"][0]
    assert error["field"] == "ids"
    assert error["code"] == ExportErrorCode.INVALID.name


@patch("saleor.plugins.manager.PluginsManager.voucher_code_export_completed")
def test_export_voucher_webhooks(
    export_completed_webhook_mock,
    staff_api_client,
    voucher_with_many_codes,
    permission_manage_discounts,
    media_root,
):
    # given
    voucher_id = graphene.Node.to_global_id("Voucher", voucher_with_many_codes.id)
    variables = {
        "input": {
            "voucherId": voucher_id,
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    # when
    staff_api_client.post_graphql(
        EXPORT_VOUCHER_CODES_MUTATION,
        variables=variables,
        permissions=[permission_manage_discounts],
    )

    # then
    export_completed_webhook_mock.assert_called_once()
