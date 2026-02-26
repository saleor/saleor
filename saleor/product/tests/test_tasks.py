import datetime
import logging
from decimal import Decimal
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone
from faker import Faker
from PIL import Image
from requests.exceptions import RequestException

from ...discount import PromotionType, RewardValueType
from ...discount.models import Promotion, PromotionRule
from ..models import (
    Product,
    ProductChannelListing,
    ProductMedia,
    ProductVariantChannelListing,
)
from ..tasks import (
    NonRetryableError,
    RetryableError,
    _get_preorder_variants_to_clean,
    fetch_product_media_image_task,
    mark_products_search_vector_as_dirty,
    recalculate_discounted_price_for_products_task,
    update_products_search_vector_task,
    update_variant_relations_for_active_promotion_rules_task,
    update_variants_names,
)
from ..utils.variants import fetch_variants_for_promotion_rules


@patch(
    "saleor.product.tasks.update_variant_relations_for_active_promotion_rules_task."
    "delay"
)
def test_update_variant_relations_for_active_promotion_rules_task(
    update_variant_relations_for_active_promotion_rules_task_mock,
    promotion_list,
    product_list,
    collection,
):
    # given
    Promotion.objects.update(start_date=timezone.now() - datetime.timedelta(days=1))
    PromotionRule.objects.update(variants_dirty=True)
    PromotionRuleVariant = PromotionRule.variants.through
    PromotionRuleVariant.objects.all().delete()
    products_with_promotions = product_list[1:]
    collection.products.add(*products_with_promotions)

    # when
    update_variant_relations_for_active_promotion_rules_task()

    # then
    listing_marked_as_dirty = ProductChannelListing.objects.filter(
        product__in=products_with_promotions, discounted_price_dirty=True
    ).values_list("id", flat=True)
    all_product_listings = ProductChannelListing.objects.filter(
        product__in=products_with_promotions
    ).values_list("id", flat=True)
    assert listing_marked_as_dirty
    assert set(listing_marked_as_dirty) == set(all_product_listings)
    assert set(
        PromotionRuleVariant.objects.values_list("promotionrule_id", flat=True)
    ) == set(PromotionRule.objects.values_list("id", flat=True))
    assert update_variant_relations_for_active_promotion_rules_task_mock.called


@patch(
    "saleor.product.tasks.update_variant_relations_for_active_promotion_rules_task."
    "delay"
)
def test_update_variant_relations_for_active_promotion_rules_task_when_not_valid(
    update_variant_relations_for_active_promotion_rules_task_mock,
    product_list,
    category,
    channel_USD,
):
    # given
    category.metadata = {"test": "test"}
    category.save(update_fields=["metadata"])

    promotion = Promotion.objects.create(
        name="Promotion",
        type=PromotionType.CATALOGUE,
        end_date=timezone.now() + datetime.timedelta(days=30),
    )
    rule = promotion.rules.create(
        name="Percentage promotion rule",
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal(10),
        catalogue_predicate={
            "categoryPredicate": {"metadata": [{"key": "test", "value": "test"}]}
        },
    )
    rule.channels.add(channel_USD)
    fetch_variants_for_promotion_rules(promotion.rules.all())

    PromotionRule.objects.update(variants_dirty=True)
    category.metadata = {}
    category.save(update_fields=["metadata"])

    # when
    update_variant_relations_for_active_promotion_rules_task()

    # then
    product_ids_in_category = Product.objects.filter(category=category).values_list(
        "id", flat=True
    )
    assert ProductChannelListing.objects.filter(
        product_id__in=product_ids_in_category, discounted_price_dirty=True
    ).count() == len(product_ids_in_category)


@patch("saleor.product.tasks.PROMOTION_RULE_BATCH_SIZE", 1)
def test_update_variant_relations_for_active_promotion_rules_task_with_order_predicate(
    order_promotion_rule,
):
    # given
    Promotion.objects.update(start_date=timezone.now() - datetime.timedelta(days=1))
    PromotionRule.objects.update(catalogue_predicate={})

    # when
    update_variant_relations_for_active_promotion_rules_task()

    # then
    assert PromotionRule.objects.filter(variants_dirty=True).count() == 0


@pytest.mark.parametrize("reward_value", [None, 0])
@patch("saleor.product.tasks.PROMOTION_RULE_BATCH_SIZE", 1)
@patch("saleor.product.tasks.recalculate_discounted_price_for_products_task.delay")
@patch("saleor.product.utils.variants.fetch_variants_for_promotion_rules")
def test_update_variant_relations_for_active_promotion_rules_with_empty_reward_value(
    fetch_variants_for_promotion_rules_mock,
    recalculate_discounted_price_for_products_task_mock,
    reward_value,
    promotion_list,
    collection,
    product_list,
):
    # given
    Promotion.objects.update(start_date=timezone.now() - datetime.timedelta(days=1))
    PromotionRuleVariant = PromotionRule.variants.through
    PromotionRuleVariant.objects.all().delete()

    collection.products.add(*product_list[1:])

    rule = PromotionRule.objects.first()
    rule.variants_dirty = False
    rule.reward_value = reward_value
    rule.save(update_fields=["reward_value"])

    # when
    recalculate_discounted_price_for_products_task()

    # then
    assert not fetch_variants_for_promotion_rules_mock.called
    assert not recalculate_discounted_price_for_products_task_mock.called


@patch("saleor.product.tasks.recalculate_discounted_price_for_products_task.delay")
def test_recalculate_discounted_price_for_products_task(
    recalculate_discounted_price_for_products_task_mock,
    product_list,
):
    # given
    ProductChannelListing.objects.update(
        discounted_price_amount=0, discounted_price_dirty=True
    )
    ProductVariantChannelListing.objects.update(discounted_price_amount=0)

    # when
    recalculate_discounted_price_for_products_task()

    # then
    assert not ProductChannelListing.objects.filter(discounted_price_amount=0).exists()
    assert not ProductVariantChannelListing.objects.filter(
        discounted_price_amount=0
    ).exists()
    assert recalculate_discounted_price_for_products_task_mock.called


@patch("saleor.product.tasks.update_discounted_prices_for_promotion")
@patch("saleor.product.tasks.recalculate_discounted_price_for_products_task.delay")
def test_recalculate_discounted_price_for_products_task_with_correct_prices(
    recalculate_discounted_price_for_products_task_mock,
    update_discounted_prices_for_promotion_mock,
    product_list,
):
    # given
    ProductChannelListing.objects.update(discounted_price_dirty=False)

    # when
    recalculate_discounted_price_for_products_task()

    # then
    assert not recalculate_discounted_price_for_products_task_mock.called
    assert not update_discounted_prices_for_promotion_mock.called


@patch("saleor.product.tasks.update_discounted_prices_for_promotion")
@patch("saleor.product.tasks.recalculate_discounted_price_for_products_task.delay")
def test_recalculate_discounted_price_for_products_task_updates_only_dirty_listings(
    recalculate_discounted_price_for_products_task_mock,
    update_discounted_prices_for_promotion_mock,
    product_list,
):
    # given

    listings = ProductChannelListing.objects.all()
    assert listings.count() != 1

    listing_marked_as_dirty = listings.first()
    listing_marked_as_dirty.discounted_price_dirty = True
    listing_marked_as_dirty.save(update_fields=["discounted_price_dirty"])

    # when
    recalculate_discounted_price_for_products_task()

    # then
    assert update_discounted_prices_for_promotion_mock.called
    recalculate_discounted_price_for_products_task_mock.assert_called_once_with()


@patch("saleor.product.tasks.recalculate_discounted_price_for_products_task.delay")
@patch("saleor.product.tasks.PROMOTION_RULE_BATCH_SIZE", 1)
def test_recalculate_discounted_price_for_products_task_re_trigger_task(
    recalculate_discounted_price_for_products_task_mock,
    product_list,
):
    # given
    ProductChannelListing.objects.update(discounted_price_dirty=True)

    # when
    recalculate_discounted_price_for_products_task()

    # then
    assert recalculate_discounted_price_for_products_task_mock.called


def test_update_variants_names(product_variant_list, size_attribute):
    # given
    variant_without_name = product_variant_list[0]
    variant_with_name = product_variant_list[1]
    random_name = Faker().word()
    variant_with_name.name = random_name
    variant_with_name.save()
    product = variant_without_name.product

    # when
    update_variants_names(product.product_type_id, [size_attribute.id])

    # then
    variant_without_name.refresh_from_db()
    variant_with_name.refresh_from_db()
    assert variant_without_name.name == variant_without_name.sku
    assert variant_with_name.name == random_name


def test_update_variants_names_product_type_does_not_exist(caplog):
    # given
    caplog.set_level(logging.WARNING)
    product_type_id = -1

    # when
    update_variants_names(product_type_id, [])

    # then
    assert f"Cannot find product type with id: {product_type_id}" in caplog.text


def test_get_preorder_variants_to_clean(
    variant,
    preorder_variant_global_threshold,
    preorder_variant_channel_threshold,
    preorder_variant_global_and_channel_threshold,
):
    preorder_variant_before_end_date = preorder_variant_channel_threshold
    preorder_variant_before_end_date.preorder_end_date = (
        timezone.now() + datetime.timedelta(days=1)
    )
    preorder_variant_before_end_date.save(update_fields=["preorder_end_date"])

    preorder_variant_after_end_date = preorder_variant_global_and_channel_threshold
    preorder_variant_after_end_date.preorder_end_date = (
        timezone.now() - datetime.timedelta(days=1)
    )
    preorder_variant_after_end_date.save(update_fields=["preorder_end_date"])

    variants_to_clean = _get_preorder_variants_to_clean()
    assert len(variants_to_clean) == 1
    assert variants_to_clean[0] == preorder_variant_after_end_date


def test_update_products_search_vector_task(product):
    # given
    product.search_index_dirty = True
    product.save(update_fields=["search_index_dirty"])

    # when
    update_products_search_vector_task()
    product.refresh_from_db(fields=["search_index_dirty"])

    # then
    assert product.search_index_dirty is False


@pytest.mark.parametrize("dirty_products_number", [0, 1, 2, 3])
def test_update_products_search_vector_task_with_static_number_of_queries(
    product, product_list, dirty_products_number, django_assert_num_queries
):
    # given
    product.search_index_dirty = True
    product.save()
    for i in range(dirty_products_number):
        product_list[i].search_index_dirty = True
        product_list[i].save(update_fields=["search_index_dirty"])

    # when & # then
    with django_assert_num_queries(16):
        update_products_search_vector_task()


@pytest.mark.slow
@pytest.mark.limit_memory("50 MB")
def test_mem_usage_recalculate_discounted_price_for_products_task(
    lots_of_products_with_variants,
):
    recalculate_discounted_price_for_products_task()


def test_mark_products_search_vector_as_dirty(product_list):
    # given
    product_ids = [product.id for product in product_list]
    Product.objects.all().update(search_index_dirty=False)

    # when
    mark_products_search_vector_as_dirty(product_ids)

    # then
    assert all(
        Product.objects.filter(id__in=product_ids).values_list(
            "search_index_dirty", flat=True
        )
    )


def test_fetch_product_media_image_already_has_image(product_media_image, caplog):
    # given
    caplog.set_level(logging.WARNING)
    assert product_media_image.image

    image = product_media_image.image

    # when
    fetch_product_media_image_task(product_media_image.pk)

    # then
    assert "already has an image" in caplog.text

    product_media_image.refresh_from_db(fields=["image"])
    assert product_media_image.image == image


def test_fetch_product_media_image_not_found(caplog):
    # given
    caplog.set_level(logging.WARNING)
    non_existent_id = -1
    assert not ProductMedia.objects.filter(pk=non_existent_id).exists()

    # when
    fetch_product_media_image_task(non_existent_id)

    # then
    assert "Cannot find product media" in caplog.text


def test_fetch_product_media_image_missing_external_url_and_image(
    product_media_image_not_yet_fetched,
):
    # given
    product_media = product_media_image_not_yet_fetched
    product_media.external_url = None
    product_media.save(update_fields=["external_url"])
    assert not product_media.image

    # when & then
    with pytest.raises(NonRetryableError, match="invalid state"):
        fetch_product_media_image_task(product_media.pk)


def test_fetch_product_media_image_wrong_type(product_media_video, caplog):
    # given
    caplog.set_level(logging.WARNING)
    product_media = product_media_video
    assert not product_media.image

    # when
    fetch_product_media_image_task(product_media.pk)

    # then
    assert "Cannot find product media" in caplog.text
    product_media.refresh_from_db()
    assert not product_media.image


@patch("saleor.product.tasks.HTTPClient")
def test_fetch_product_media_image_non_image_content_type(
    mock_http_client,
    product_media_image_not_yet_fetched,
    caplog,
):
    # given
    product_media = product_media_image_not_yet_fetched
    assert product_media.external_url
    assert not product_media.image

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers.get.return_value = "text/plain"
    mock_http_client.send_request.return_value.__enter__ = MagicMock(
        return_value=mock_response
    )

    # when
    fetch_product_media_image_task(product_media.pk)

    # then
    assert "does not have valid image content-type" in caplog.text
    product_media.refresh_from_db()
    assert not product_media.image


def test_fetch_product_media_image_success(
    product_media_image_not_yet_fetched, media_root
):
    # given
    product_media = product_media_image_not_yet_fetched
    assert product_media.external_url
    assert not product_media.image

    image_buffer = BytesIO()
    Image.new("RGB", (1, 1)).save(image_buffer, format="JPEG")
    image_bytes = image_buffer.getvalue()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers.get.return_value = "image/jpeg"
    mock_response.content = image_bytes

    # when
    with patch("saleor.product.tasks.HTTPClient") as mock_http_client:
        mock_http_client.send_request.return_value.__enter__ = MagicMock(
            return_value=mock_response
        )
        fetch_product_media_image_task(product_media.pk)

    # then
    product_media.refresh_from_db()
    assert product_media.external_url is None
    assert product_media.image


@patch("saleor.product.tasks.HTTPClient")
def test_fetch_product_media_image_unsupported_image_content_type(
    mock_http_client,
    product_media_image_not_yet_fetched,
    caplog,
):
    # given
    product_media = product_media_image_not_yet_fetched
    assert not product_media.image

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers.get.return_value = "image/svg+xml"
    mock_http_client.send_request.return_value.__enter__ = MagicMock(
        return_value=mock_response
    )

    # when
    fetch_product_media_image_task(product_media.pk)

    # then
    assert "does not have valid image content-type" in caplog.text
    product_media.refresh_from_db()
    assert not product_media.image


@patch("saleor.product.tasks.HTTPClient")
def test_fetch_product_media_image_request_exception(
    mock_http_client,
    product_media_image_not_yet_fetched,
    caplog,
):
    # given
    caplog.set_level(logging.WARNING)
    product_media = product_media_image_not_yet_fetched
    assert product_media.external_url
    assert not product_media.image

    # when
    with (
        patch("saleor.product.tasks.HTTPClient") as mock_http_client,
    ):
        mock_http_client.send_request.side_effect = RequestException(
            "Connection timeout"
        )
        fetch_product_media_image_task(product_media.pk)

    # then
    assert "Connection timeout" in caplog.text
    product_media.refresh_from_db()
    assert not product_media.image
    assert product_media.external_url


def test_fetch_product_media_image_deleted_after_final_retry(
    product_media_image_not_yet_fetched, caplog
):
    # given
    caplog.set_level(logging.WARNING)
    product_media = product_media_image_not_yet_fetched
    assert not product_media.image

    max_retries = 3
    assert fetch_product_media_image_task.max_retries == max_retries

    # when

    # simulate the state where task is being retried for the third time
    request = MagicMock(retries=max_retries)
    with (
        patch("saleor.product.tasks.HTTPClient") as mock_http_client,
        patch.object(
            fetch_product_media_image_task, "request_stack", MagicMock(top=request)
        ),
    ):
        mock_http_client.send_request.side_effect = ConnectionError("Connection error")
        fetch_product_media_image_task(product_media.pk)

    # then
    assert "Removing product media" in caplog.text
    assert not ProductMedia.objects.filter(pk=product_media.pk).exists()


def test_fetch_product_media_image_invalid_exif(
    product_media_image_not_yet_fetched,
    caplog,
):
    # given
    product_media = product_media_image_not_yet_fetched
    assert not product_media.image

    image_buffer = BytesIO()
    Image.new("RGB", (1, 1)).save(image_buffer, format="JPEG")
    image_bytes = image_buffer.getvalue()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers.get.return_value = "image/jpeg"
    mock_response.content = image_bytes

    # when
    with (
        patch("saleor.product.tasks.HTTPClient") as mock_http_client,
        patch("saleor.product.utils.tasks_utils.Image.open") as mock_image_open,
    ):
        mock_http_client.send_request.return_value.__enter__ = MagicMock(
            return_value=mock_response
        )
        mock_pil_image = MagicMock()
        mock_pil_image.getexif.side_effect = SyntaxError("Invalid EXIF")
        mock_image_open.return_value = mock_pil_image

        fetch_product_media_image_task(product_media.pk)

    # then
    assert "Invalid EXIF" in caplog.text
    product_media.refresh_from_db()
    assert not product_media.image


def test_fetch_product_media_image_invalid_metadata(
    product_media_image_not_yet_fetched,
    caplog,
):
    # given
    product_media = product_media_image_not_yet_fetched
    assert not product_media.image

    image_buffer = BytesIO()
    Image.new("RGB", (1, 1)).save(image_buffer, format="JPEG")
    image_bytes = image_buffer.getvalue()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers.get.return_value = "image/jpeg"
    mock_response.content = image_bytes

    # when
    with (
        patch("saleor.product.tasks.HTTPClient") as mock_http_client,
        patch(
            "saleor.product.utils.tasks_utils.ProcessedImage.get_image_metadata_from_file",
            side_effect=ValueError("Unsupported image MIME type"),
        ),
    ):
        mock_http_client.send_request.return_value.__enter__ = MagicMock(
            return_value=mock_response
        )

        fetch_product_media_image_task(product_media.pk)

    # then
    assert "Unsupported image MIME type" in caplog.text
    product_media.refresh_from_db()
    assert not product_media.image


@pytest.mark.parametrize("status_code", [500, 502, 503])
def test_fetch_product_media_image_server_error_triggers_retry(
    product_media_image_not_yet_fetched,
    status_code,
):
    # given
    product_media = product_media_image_not_yet_fetched

    mock_response = MagicMock()
    mock_response.status_code = status_code

    # when & then
    with (
        patch("saleor.product.tasks.HTTPClient") as mock_http_client,
    ):
        mock_http_client.send_request.return_value.__enter__ = MagicMock(
            return_value=mock_response
        )
        with pytest.raises(RetryableError):
            fetch_product_media_image_task(product_media.pk)

    # then
    product_media.refresh_from_db()
    assert not product_media.image
    assert product_media.external_url


@pytest.mark.parametrize("status_code", [100, 199, 401, 404, 499])
def test_fetch_product_media_image_client_error_does_not_retry(
    product_media_image_not_yet_fetched,
    caplog,
    status_code,
):
    # given
    product_media = product_media_image_not_yet_fetched

    mock_response = MagicMock()
    mock_response.status_code = status_code

    # when
    with patch("saleor.product.tasks.HTTPClient") as mock_http_client:
        mock_http_client.send_request.return_value.__enter__ = MagicMock(
            return_value=mock_response
        )
        fetch_product_media_image_task(product_media.pk)

    # then
    assert f"HTTP status: {status_code}" in caplog.text
    product_media.refresh_from_db()
    assert not product_media.image
    assert product_media.external_url
