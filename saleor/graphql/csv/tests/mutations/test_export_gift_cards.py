from unittest.mock import ANY, patch

import graphene
import pytest

from .....csv import ExportEvents
from .....csv.error_codes import ExportErrorCode
from .....csv.models import ExportEvent
from ....tests.utils import get_graphql_content
from ...enums import ExportScope, FileTypeEnum

EXPORT_GIFT_CARDS_MUTATION = """
    mutation ExportGiftCards($input: ExportGiftCardsInput!){
        exportGiftCards(input: $input){
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
        (
            {
                "scope": ExportScope.FILTER.name,
                "filter": {"tags": ["abc"]},
                "fileType": FileTypeEnum.CSV.name,
            },
            {"filter": {"tags": ["abc"]}},
        ),
    ],
)
@patch("saleor.graphql.csv.mutations.export_gift_cards.export_gift_cards_task.delay")
def test_export_gift_cards_mutation(
    export_gift_cards_mock,
    input,
    called_data,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    permission_manage_gift_card,
    permission_manage_apps,
):
    query = EXPORT_GIFT_CARDS_MUTATION
    user = staff_api_client.user
    variables = {"input": input}

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[permission_manage_gift_card, permission_manage_apps],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportGiftCards"]
    export_file_data = data["exportFile"]

    export_gift_cards_mock.assert_called_once_with(
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


@patch("saleor.graphql.csv.mutations.export_gift_cards.export_gift_cards_task.delay")
def test_export_gift_cards_mutation_ids_scope(
    export_gift_cards_mock,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_staff,
):
    query = EXPORT_GIFT_CARDS_MUTATION
    user = staff_api_client.user

    gift_cards = [gift_card_expiry_date, gift_card_used]

    ids = [graphene.Node.to_global_id("GiftCard", card.pk) for card in gift_cards]

    variables = {
        "input": {
            "scope": ExportScope.IDS.name,
            "ids": ids,
            "fileType": FileTypeEnum.XLSX.name,
        }
    }

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_apps,
            permission_manage_staff,
        ],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportGiftCards"]
    export_file_data = data["exportFile"]

    export_gift_cards_mock.assert_called_once()
    (
        call_args,
        call_kwargs,
    ) = export_gift_cards_mock.call_args

    assert set(call_args[1]["ids"]) == {str(card.pk) for card in gift_cards}
    assert call_args[2] == FileTypeEnum.XLSX.value

    assert not data["errors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["user"]["email"] == staff_api_client.user.email
    assert export_file_data["app"] is None
    assert ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
    ).exists()


@patch("saleor.graphql.csv.mutations.export_gift_cards.export_gift_cards_task.delay")
def test_export_gift_cards_mutation_ids_scope_invalid_object_type(
    export_gift_cards_mock,
    staff_api_client,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_staff,
):
    query = EXPORT_GIFT_CARDS_MUTATION
    user = staff_api_client.user

    gift_cards = [gift_card_expiry_date, gift_card_used]

    ids = [graphene.Node.to_global_id("Product", card.pk) for card in gift_cards]

    variables = {
        "input": {
            "scope": ExportScope.IDS.name,
            "ids": ids,
            "fileType": FileTypeEnum.CSV.name,
        }
    }

    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_apps,
            permission_manage_staff,
        ],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportGiftCards"]

    errors = data["errors"]
    assert len(errors) == 1
    assert not data["exportFile"]
    assert errors[0]["field"] == "ids"
    assert errors[0]["code"] == ExportErrorCode.GRAPHQL_ERROR.name

    assert not ExportEvent.objects.filter(
        user=user, app=None, type=ExportEvents.EXPORT_PENDING
    )

    export_gift_cards_mock.assert_not_called()


@pytest.mark.parametrize(
    "input, error_field",
    [
        (
            {
                "scope": ExportScope.FILTER.name,
                "fileType": FileTypeEnum.CSV.name,
            },
            "filter",
        ),
        (
            {
                "scope": ExportScope.IDS.name,
                "fileType": FileTypeEnum.CSV.name,
            },
            "ids",
        ),
    ],
)
@patch("saleor.graphql.csv.mutations.export_gift_cards.export_gift_cards_task.delay")
def test_export_gift_cards_mutation_failed(
    export_gift_cards_mock,
    input,
    error_field,
    app_api_client,
    gift_card,
    gift_card_expiry_date,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_staff,
):
    query = EXPORT_GIFT_CARDS_MUTATION
    app = app_api_client.app

    variables = {"input": input}

    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_apps,
            permission_manage_staff,
        ],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportGiftCards"]

    errors = data["errors"]
    assert len(errors) == 1
    assert not data["exportFile"]
    assert errors[0]["field"] == error_field
    assert errors[0]["code"] == ExportErrorCode.REQUIRED.name

    assert not ExportEvent.objects.filter(
        user=None, app=app, type=ExportEvents.EXPORT_PENDING
    )

    export_gift_cards_mock.assert_not_called()


EXPORT_GIFT_CARDS_MUTATION_BY_APP = """
    mutation ExportGiftCards($input: ExportGiftCardsInput!){
        exportGiftCards(input: $input){
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


@patch("saleor.graphql.csv.mutations.export_gift_cards.export_gift_cards_task.delay")
def test_export_gift_cards_mutation_by_app(
    export_gift_cards_mock,
    app_api_client,
    gift_card,
    gift_card_expiry_date,
    permission_manage_gift_card,
    permission_manage_apps,
    permission_manage_staff,
):
    query = EXPORT_GIFT_CARDS_MUTATION_BY_APP
    app = app_api_client.app
    variables = {
        "input": {
            "scope": ExportScope.ALL.name,
            "fileType": FileTypeEnum.XLSX.name,
        }
    }

    response = app_api_client.post_graphql(
        query,
        variables=variables,
        permissions=[
            permission_manage_gift_card,
            permission_manage_apps,
        ],
    )
    content = get_graphql_content(response)
    data = content["data"]["exportGiftCards"]
    export_file_data = data["exportFile"]

    export_gift_cards_mock.assert_called_once_with(
        ANY, {"all": ""}, FileTypeEnum.XLSX.value
    )

    assert not data["errors"]
    assert data["exportFile"]["id"]
    assert export_file_data["createdAt"]
    assert export_file_data["app"]["name"] == app.name
    assert ExportEvent.objects.filter(
        user=None, app=app, type=ExportEvents.EXPORT_PENDING
    ).exists()
