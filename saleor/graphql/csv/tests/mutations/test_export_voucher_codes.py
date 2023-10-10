from unittest.mock import ANY, patch

import graphene
import pytest

from .....csv import ExportEvents
from .....csv.error_codes import ExportErrorCode
from .....csv.models import ExportEvent
from ....tests.utils import get_graphql_content
from ...enums import ExportScope, FileTypeEnum

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


@pytest.mark.parametrize(
    "input, called_data",
    [
        (
            {
                "scope": ExportScope.ALL.name,
                "fileType": FileTypeEnum.CSV.name,
            },
            {"all": ""},
        ),
        # (
        #     {
        #         "scope": ExportScope.FILTER.name,
        #         "filter": {"tags": ["abc"]},
        #         "fileType": FileTypeEnum.CSV.name,
        #     },
        #     {"filter": {"tags": ["abc"]}},
        # ),
    ],
)
@patch(
    "saleor.graphql.csv.mutations.export_voucher_codes.export_voucher_codes_task.delay"
)
def test_export_voucher_codes(
    export_voucher_codes_mock,
    input,
    called_data,
    staff_api_client,
    voucher_with_many_codes,
    permission_manage_apps,
    permission_manage_discounts,
):
    user = staff_api_client.user
    voucher_id = graphene.Node.to_global_id("Voucher", voucher_with_many_codes.id)
    input["voucherId"] = voucher_id
    variables = {"input": input}
    response = staff_api_client.post_graphql(
        EXPORT_VOUCHER_CODES_MUTATION,
        variables=variables,
        permissions=[permission_manage_discounts, permission_manage_apps],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportVoucherCodes"]
    export_file_data = data["exportFile"]

    export_voucher_codes_mock.assert_called_once_with(
        ANY, called_data, FileTypeEnum.CSV.value
    )

    assert not data["errors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"]["email"] == staff_api_client.user.email
    assert export_file_data["app"] is None
    assert ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
    ).exists()
