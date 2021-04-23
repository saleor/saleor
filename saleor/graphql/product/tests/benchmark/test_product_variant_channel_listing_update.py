import graphene
import pytest

from .....product.models import ProductChannelListing, ProductMedia, VariantMedia
from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_variant_channel_listing_update(
    staff_api_client,
    settings,
    product_with_variant_with_two_attributes,
    permission_manage_products,
    channel_USD,
    channel_PLN,
    image,
    media_root,
    count_queries,
):
    # given
    query = """
        mutation UpdateProductVariantChannelListing(
            $id: ID!,
            $input: [ProductVariantChannelListingAddInput!]!
        ) {
            productVariantChannelListingUpdate(id: $id, input: $input) {
                errors {
                    field
                    message
                    code
                    channels
                }
                variant {
                    id
                    channelListings {
                        channel {
                            id
                            slug
                            currencyCode
                        }
                        price {
                            amount
                            currency
                        }
                        costPrice {
                            amount
                            currency
                        }
                        margin
                    }
                }
            }
        }
    """
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    product = product_with_variant_with_two_attributes
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_PLN,
        is_published=True,
    )
    variant = product.variants.get()
    product_image = ProductMedia.objects.create(product=product, image=image)
    VariantMedia.objects.create(variant=variant, media=product_image)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    channel_usd_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    channel_pln_id = graphene.Node.to_global_id("Channel", channel_PLN.id)
    price = 1
    second_price = 20
    variables = {
        "id": variant_id,
        "input": [
            {"channelId": channel_usd_id, "price": price, "costPrice": price},
            {
                "channelId": channel_pln_id,
                "price": second_price,
                "costPrice": second_price,
            },
        ],
    }

    # when
    response = staff_api_client.post_graphql(
        query,
        variables=variables,
        permissions=(permission_manage_products,),
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVariantChannelListingUpdate"]
    assert not data["errors"]
