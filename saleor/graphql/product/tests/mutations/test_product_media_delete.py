from unittest.mock import patch

import graphene
import pytest

from .....graphql.tests.utils import get_graphql_content


@patch("saleor.plugins.manager.PluginsManager.product_media_deleted")
@patch("saleor.plugins.manager.PluginsManager.product_updated")
@patch("saleor.product.signals.delete_from_storage_task.delay")
def test_product_media_delete(
    delete_from_storage_task_mock,
    product_updated_mock,
    product_media_deleted_mock,
    staff_api_client,
    product_with_image,
    permission_manage_products,
):
    # given
    product = product_with_image
    query = """
            mutation deleteProductMedia($id: ID!) {
                productMediaDelete(id: $id) {
                    media {
                        id
                        url(size: 0)
                    }
                }
            }
        """
    media_obj = product.media.first()
    media_img_path = media_obj.image.name
    node_id = graphene.Node.to_global_id("ProductMedia", media_obj.id)
    variables = {"id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productMediaDelete"]
    assert media_obj.image.url in data["media"]["url"]
    product_media_deleted_mock.assert_called_once_with(media_obj)

    with pytest.raises(media_obj._meta.model.DoesNotExist):
        media_obj.refresh_from_db()
    assert node_id == data["media"]["id"]
    product_updated_mock.assert_called_once_with(product)
    delete_from_storage_task_mock.assert_called_once_with(media_img_path)
