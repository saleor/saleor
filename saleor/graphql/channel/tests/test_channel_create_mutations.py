from django.utils.text import slugify

from ....channel.error_codes import ChannelErrorCode
from ....channel.models import Channel
from ...tests.utils import assert_no_permission, get_graphql_content

CHANNEL_CREATE_MUTATION = """
    mutation CreateChannel($input: ChannelCreateInput!){
        channelCreate(input: $input){
            channel{
                id
                name
                slug
                currencyCode
            }
            channelErrors{
                field
                code
                message
            }
        }
    }
"""


def test_channel_create_mutation_as_staff_user(
    permission_manage_channels,
    staff_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    variables = {"input": {"name": name, "slug": slug, "currencyCode": currency_code}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["channelErrors"]
    channel_data = data["channel"]
    channel = Channel.objects.get()
    assert channel_data["name"] == channel.name == name
    assert channel_data["slug"] == channel.slug == slug
    assert channel_data["currencyCode"] == channel.currency_code == currency_code


def test_channel_create_mutation_as_app(
    permission_manage_channels,
    app_api_client,
):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    variables = {"input": {"name": name, "slug": slug, "currencyCode": currency_code}}

    # when
    response = app_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["channelCreate"]
    assert not data["channelErrors"]
    channel_data = data["channel"]
    channel = Channel.objects.get()
    assert channel_data["name"] == channel.name == name
    assert channel_data["slug"] == channel.slug == slug
    assert channel_data["currencyCode"] == channel.currency_code == currency_code


def test_channel_create_mutation_as_customer(user_api_client):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    variables = {"input": {"name": name, "slug": slug, "currencyCode": currency_code}}

    # when
    response = user_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(),
    )

    # then
    assert_no_permission(response)


def test_channel_create_mutation_as_anonymous(api_client):
    # given
    name = "testName"
    slug = "test_slug"
    currency_code = "USD"
    variables = {"input": {"name": name, "slug": slug, "currencyCode": currency_code}}

    # when
    response = api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(),
    )

    # then
    assert_no_permission(response)


def test_channel_create_mutation_slugify_slug_field(
    permission_manage_channels,
    staff_api_client,
):
    # given
    name = "testName"
    slug = "Invalid slug"
    currency_code = "USD"
    variables = {"input": {"name": name, "slug": slug, "currencyCode": currency_code}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    channel_data = content["data"]["channelCreate"]["channel"]
    assert channel_data["slug"] == slugify(slug)


def test_channel_create_mutation_with_duplicated_slug(
    permission_manage_channels, staff_api_client, channel_USD
):
    # given
    name = "New Channel"
    slug = channel_USD.slug
    currency_code = "USD"
    variables = {"input": {"name": name, "slug": slug, "currencyCode": currency_code}}

    # when
    response = staff_api_client.post_graphql(
        CHANNEL_CREATE_MUTATION,
        variables=variables,
        permissions=(permission_manage_channels,),
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["channelCreate"]["channelErrors"][0]
    assert error["field"] == "slug"
    assert error["code"] == ChannelErrorCode.UNIQUE.name
