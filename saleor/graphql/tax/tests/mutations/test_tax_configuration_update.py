import graphene
import pytest
from django.test import override_settings

from .....core.tests.test_taxes import app_factory, tax_app_factory  # noqa: F401
from .....plugins import PLUGIN_IDENTIFIER_PREFIX
from .....plugins.tests.sample_plugins import PluginSample
from .....tax.error_codes import TaxConfigurationUpdateErrorCode
from .....tax.models import TaxConfiguration
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import TaxCalculationStrategy
from ..fragments import TAX_CONFIGURATION_FRAGMENT

MUTATION = (
    """
    mutation TaxConfigurationUpdate(
        $id: ID!
        $input: TaxConfigurationUpdateInput!
    ) {
        taxConfigurationUpdate(id: $id, input: $input) {
            errors {
                field
                message
                code
                countryCodes
            }
            taxConfiguration {
                ...TaxConfiguration
            }
        }
    }
"""
    + TAX_CONFIGURATION_FRAGMENT
)


def _test_no_permissions(api_client):
    # given
    tax_configuration = TaxConfiguration.objects.first()
    id = graphene.Node.to_global_id("TaxConfiguration", tax_configuration.pk)
    variables = {"id": id, "input": {}}

    # when
    response = api_client.post_graphql(MUTATION, variables, permissions=[])

    # then
    assert_no_permission(response)


def test_no_permission_staff(channel_USD, staff_api_client):
    _test_no_permissions(staff_api_client)


def test_no_permission_app(channel_USD, app_api_client):
    _test_no_permissions(app_api_client)


@pytest.fixture
def example_tax_configuration(channel_USD):
    channel_USD.tax_configuration.delete()
    tax_configuration = TaxConfiguration.objects.create(
        channel=channel_USD,
        charge_taxes=True,
        display_gross_prices=True,
        prices_entered_with_tax=True,
    )
    tax_configuration.country_exceptions.create(
        country="PL", charge_taxes=True, display_gross_prices=True
    )
    return tax_configuration


def _test_tax_configuration_update(
    example_tax_configuration, api_client, permission_manage_taxes
):
    # given
    id = graphene.Node.to_global_id("TaxConfiguration", example_tax_configuration.pk)
    variables = {
        "id": id,
        "input": {
            "chargeTaxes": False,
            "taxCalculationStrategy": TaxCalculationStrategy.FLAT_RATES.value,
            "displayGrossPrices": False,
            "pricesEnteredWithTax": False,
            "updateCountriesConfiguration": [
                {
                    "countryCode": "PL",
                    "chargeTaxes": False,
                    "displayGrossPrices": False,
                    "taxCalculationStrategy": TaxCalculationStrategy.FLAT_RATES.value,
                }
            ],
            "removeCountriesConfiguration": [],
        },
    }

    # when
    response = api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxConfigurationUpdate"]
    assert not data["errors"]
    assert data["taxConfiguration"]["id"] == id
    assert data["taxConfiguration"]["chargeTaxes"] is False
    assert (
        data["taxConfiguration"]["taxCalculationStrategy"]
        == TaxCalculationStrategy.FLAT_RATES.name
    )
    assert data["taxConfiguration"]["displayGrossPrices"] is False
    assert data["taxConfiguration"]["pricesEnteredWithTax"] is False
    assert data["taxConfiguration"]["countries"][0]["chargeTaxes"] is False
    assert (
        data["taxConfiguration"]["countries"][0]["taxCalculationStrategy"]
        == TaxCalculationStrategy.FLAT_RATES.name
    )
    assert data["taxConfiguration"]["countries"][0]["displayGrossPrices"] is False


def test_update_as_staff(
    example_tax_configuration, staff_api_client, permission_manage_taxes
):
    _test_tax_configuration_update(
        example_tax_configuration, staff_api_client, permission_manage_taxes
    )


def test_update_as_app(
    example_tax_configuration, app_api_client, permission_manage_taxes
):
    _test_tax_configuration_update(
        example_tax_configuration, app_api_client, permission_manage_taxes
    )


def test_raise_duplicate_input_item(
    example_tax_configuration, staff_api_client, permission_manage_taxes
):
    id = graphene.Node.to_global_id("TaxConfiguration", example_tax_configuration.pk)
    variables = {
        "id": id,
        "input": {
            "updateCountriesConfiguration": [
                {"countryCode": "PL", "chargeTaxes": False, "displayGrossPrices": False}
            ],
            "removeCountriesConfiguration": ["PL"],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["taxConfigurationUpdate"]["errors"]
    assert errors
    assert (
        errors[0]["code"] == TaxConfigurationUpdateErrorCode.DUPLICATED_INPUT_ITEM.name
    )
    assert errors[0]["countryCodes"] == ["PL"]


def test_create_and_update_country_configurations(
    example_tax_configuration, staff_api_client, permission_manage_taxes
):
    # given
    id = graphene.Node.to_global_id("TaxConfiguration", example_tax_configuration.pk)

    # update PL configuration and create DE configuration
    update_PL_data = {
        "countryCode": "PL",
        "chargeTaxes": False,
        "taxCalculationStrategy": TaxCalculationStrategy.FLAT_RATES.value,
        "displayGrossPrices": False,
    }
    create_DE_data = {
        "countryCode": "DE",
        "chargeTaxes": False,
        "taxCalculationStrategy": TaxCalculationStrategy.FLAT_RATES.value,
        "displayGrossPrices": False,
    }

    variables = {
        "id": id,
        "input": {
            "updateCountriesConfiguration": [
                update_PL_data,
                create_DE_data,
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxConfigurationUpdate"]["taxConfiguration"]
    assert len(data["countries"]) == 2

    response_data = []
    for item in data["countries"]:
        new_item = {**item, "countryCode": item["country"]["code"]}
        new_item.pop("country")
        response_data.append(new_item)

    update_PL_data["taxAppId"] = None
    create_DE_data["taxAppId"] = None

    assert update_PL_data in response_data
    assert create_DE_data in response_data


def test_create_and_update_country_configurations_no_tax_calculation_strategy(
    example_tax_configuration, staff_api_client, permission_manage_taxes
):
    # given
    id = graphene.Node.to_global_id("TaxConfiguration", example_tax_configuration.pk)

    # update PL configuration and create PT configuration with omitting the
    # `taxCalculationStrategy` in both inputs
    update_PL_data = {
        "countryCode": "PL",
        "chargeTaxes": False,
        "displayGrossPrices": False,
    }
    create_PT_data = {
        "countryCode": "PT",
        "chargeTaxes": False,
        "displayGrossPrices": False,
    }

    variables = {
        "id": id,
        "input": {
            "updateCountriesConfiguration": [
                update_PL_data,
                create_PT_data,
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxConfigurationUpdate"]["taxConfiguration"]
    assert len(data["countries"]) == 2

    response_data = []
    for item in data["countries"]:
        new_item = {**item, "countryCode": item["country"]["code"]}
        new_item.pop("country")
        response_data.append(new_item)

    update_PL_data["taxCalculationStrategy"] = None
    update_PL_data["taxAppId"] = None
    create_PT_data["taxCalculationStrategy"] = None
    create_PT_data["taxAppId"] = None

    assert update_PL_data in response_data
    assert create_PT_data in response_data


def test_remove_country_configurations(
    example_tax_configuration, staff_api_client, permission_manage_taxes
):
    id = graphene.Node.to_global_id("TaxConfiguration", example_tax_configuration.pk)
    variables = {
        "id": id,
        "input": {
            "removeCountriesConfiguration": ["PL"],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxConfigurationUpdate"]["taxConfiguration"]
    assert data["countries"] == []


def test_tax_configuration_update_tax_app_id(
    example_tax_configuration,
    staff_api_client,
    permission_manage_taxes,
    tax_app_factory,  # noqa: F811
):
    # given
    tax_app = tax_app_factory(name="app", is_active=True)
    country_tax_app = tax_app_factory(name="app2", is_active=True)

    id = graphene.Node.to_global_id("TaxConfiguration", example_tax_configuration.pk)
    variables = {
        "id": id,
        "input": {
            "taxAppId": tax_app.identifier,
            "updateCountriesConfiguration": [
                {
                    "countryCode": "PL",
                    "taxAppId": country_tax_app.identifier,
                    "chargeTaxes": False,
                    "displayGrossPrices": False,
                }
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxConfigurationUpdate"]["taxConfiguration"]
    assert not content["data"]["taxConfigurationUpdate"]["errors"]
    assert data["taxAppId"] == tax_app.identifier
    assert data["countries"][0]["taxAppId"] == country_tax_app.identifier


def test_tax_configuration_update_tax_app_id_with_no_tax_app(
    example_tax_configuration,
    staff_api_client,
    permission_manage_taxes,
    app_factory,  # noqa: F811
):
    # given
    app = app_factory(
        name="app",
        is_active=True,
        permissions=[],
        webhook_event_types=[],
    )

    id = graphene.Node.to_global_id("TaxConfiguration", example_tax_configuration.pk)
    variables = {
        "id": id,
        "input": {
            "taxAppId": app.identifier,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["taxConfigurationUpdate"]["errors"]
    assert errors
    assert errors[0]["message"] == "Did not found Tax App with provided taxAppId."
    assert errors[0]["code"] == TaxConfigurationUpdateErrorCode.NOT_FOUND.name


def test_tax_configuration_update_tax_app_id_with_non_existent_app(
    example_tax_configuration, staff_api_client, permission_manage_taxes
):
    # given
    id = graphene.Node.to_global_id("TaxConfiguration", example_tax_configuration.pk)
    variables = {
        "id": id,
        "input": {
            "taxAppId": "invalid",
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["taxConfigurationUpdate"]["errors"]
    assert errors
    assert errors[0]["message"] == "Did not found Tax App with provided taxAppId."
    assert errors[0]["code"] == TaxConfigurationUpdateErrorCode.NOT_FOUND.name


@override_settings(PLUGINS=["saleor.plugins.tests.sample_plugins.PluginSample"])
def test_tax_configuration_update_tax_app_id_with_plugin(
    example_tax_configuration, staff_api_client, permission_manage_taxes
):
    """Make sure that we are able to still use legacy plugin."""
    # given
    id = graphene.Node.to_global_id("TaxConfiguration", example_tax_configuration.pk)
    plugin_id = PLUGIN_IDENTIFIER_PREFIX + PluginSample.PLUGIN_ID
    variables = {
        "id": id,
        "input": {
            "taxAppId": plugin_id,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION, variables, permissions=[permission_manage_taxes]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["taxConfigurationUpdate"]["taxConfiguration"]
    assert not content["data"]["taxConfigurationUpdate"]["errors"]
    assert data["taxAppId"] == plugin_id
