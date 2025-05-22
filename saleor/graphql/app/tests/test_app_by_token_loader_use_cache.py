from unittest.mock import patch

from django.utils import timezone

from ....app.models import App, AppToken
from ...context import SaleorContext
from ..dataloaders.app import AppByTokenLoader, create_app_cache_key_from_token


@patch("saleor.graphql.app.dataloaders.app.cache")
def test_app_by_token_loader_cache_token_calculation(
    mocked_cache, app, setup_mock_for_cache
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    raw_token = "test_token"
    token, _ = app.tokens.create(
        name="test_token",
        auth_token=raw_token,
    )
    expected_cache_key = create_app_cache_key_from_token(raw_token)

    # when
    context = SaleorContext()
    app_by_token_loader = AppByTokenLoader(context)
    loaded_apps = app_by_token_loader.batch_load([raw_token])
    fetched_app = loaded_apps[0]

    # then
    cached_app_id, token_id = mocked_cache.get(expected_cache_key)
    assert token.id == token_id
    assert fetched_app.id == app.id == cached_app_id


@patch("saleor.graphql.app.dataloaders.app.cache")
def test_app_by_token_loader_invalid_token(mocked_cache, app, setup_mock_for_cache):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    raw_token = "test_token"
    expected_cache_key = create_app_cache_key_from_token(raw_token)

    # when
    context = SaleorContext()
    app_by_token_loader = AppByTokenLoader(context)
    loaded_apps = app_by_token_loader.batch_load([raw_token])
    fetched_app = loaded_apps[0]

    # then
    cached_data = mocked_cache.get(expected_cache_key)
    assert fetched_app is None
    assert cached_data is None


@patch("saleor.graphql.app.dataloaders.app.cache")
def test_app_by_token_loader_use_cached_app(mocked_cache, app, setup_mock_for_cache):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    raw_token = "test_token"
    token, _ = app.tokens.create(
        name="test_token",
        auth_token=raw_token,
    )
    expected_cache_key = create_app_cache_key_from_token(raw_token)
    mocked_cache.set(expected_cache_key, (app.id, token.id), 123)

    # when
    context = SaleorContext()
    app_by_token_loader = AppByTokenLoader(context)
    loaded_apps = app_by_token_loader.batch_load([raw_token])
    fetched_app = loaded_apps[0]

    # then
    cached_app_id, cached_token_id = mocked_cache.get(expected_cache_key)
    assert token.id == cached_token_id
    assert fetched_app.id == app.id == cached_app_id
    # Check that the cache was set only once during given test section
    mocked_cache.set.assert_called_once_with(
        expected_cache_key, (app.id, token.id), 123
    )


@patch("saleor.graphql.app.dataloaders.app.cache")
def test_app_by_token_loader_cached_app_not_active(
    mocked_cache, app, setup_mock_for_cache
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    raw_token = "test_token"
    token, _ = app.tokens.create(
        name="test_token",
        auth_token=raw_token,
    )
    app.is_active = False
    app.save(update_fields=["is_active"])
    expected_cache_key = create_app_cache_key_from_token(raw_token)
    mocked_cache.set(expected_cache_key, (app.id, token.id), 123)

    # when
    context = SaleorContext()
    app_by_token_loader = AppByTokenLoader(context)
    loaded_apps = app_by_token_loader.batch_load([raw_token])
    fetched_app = loaded_apps[0]

    # then
    cached_app_id, cached_token_id = mocked_cache.get(expected_cache_key)
    assert token.id == cached_token_id
    assert app.id == cached_app_id
    # Check that the app was not fetched from the database
    assert fetched_app is None
    # Check that the cache was set only once during given test section
    mocked_cache.set.assert_called_once_with(
        expected_cache_key, (app.id, token.id), 123
    )


@patch("saleor.graphql.app.dataloaders.app.cache")
def test_app_by_token_loader_cached_app_marked_as_removed(
    mocked_cache, app, setup_mock_for_cache
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    raw_token = "test_token"
    token, _ = app.tokens.create(
        name="test_token",
        auth_token=raw_token,
    )
    app.removed_at = timezone.now()
    app.save(update_fields=["removed_at"])
    expected_cache_key = create_app_cache_key_from_token(raw_token)
    mocked_cache.set(expected_cache_key, (app.id, token.id), 123)

    # when
    context = SaleorContext()
    app_by_token_loader = AppByTokenLoader(context)
    loaded_apps = app_by_token_loader.batch_load([raw_token])
    fetched_app = loaded_apps[0]

    # then
    cached_app_id, cached_token_id = mocked_cache.get(expected_cache_key)
    assert token.id == cached_token_id
    assert app.id == cached_app_id
    # Check that the app was not fetched from the database
    assert fetched_app is None
    # Check that the cache was set only once during given test section
    mocked_cache.set.assert_called_once_with(
        expected_cache_key, (app.id, token.id), 123
    )


@patch("saleor.graphql.app.dataloaders.app.cache")
def test_app_by_token_loader_missing_app(mocked_cache, app, setup_mock_for_cache):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    raw_token = "test_token"
    token, _ = app.tokens.create(
        name="test_token",
        auth_token=raw_token,
    )
    deleted_app_id = app.id
    app.delete()
    expected_cache_key = create_app_cache_key_from_token(raw_token)
    mocked_cache.set(expected_cache_key, (deleted_app_id, token.id), 123)

    # when
    context = SaleorContext()
    app_by_token_loader = AppByTokenLoader(context)
    loaded_apps = app_by_token_loader.batch_load([raw_token])
    fetched_app = loaded_apps[0]

    # then
    # Check that the app was removed from the database
    assert not App.objects.exists()
    # Check that the app was not fetched from the database
    assert fetched_app is None
    # Check that the cache was set only once during given test section
    mocked_cache.set.assert_called_once_with(
        expected_cache_key, (deleted_app_id, token.id), 123
    )
    # Check if the token was removed from the cache
    assert mocked_cache.get(expected_cache_key) is None


@patch("saleor.graphql.app.dataloaders.app.cache")
def test_app_by_token_loader_removed_token(mocked_cache, app, setup_mock_for_cache):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    raw_token = "test_token"
    token, _ = app.tokens.create(
        name="test_token",
        auth_token=raw_token,
    )
    token_id = token.id
    token.delete()
    expected_cache_key = create_app_cache_key_from_token(raw_token)
    mocked_cache.set(expected_cache_key, (app.id, token_id), 123)

    # when
    context = SaleorContext()
    app_by_token_loader = AppByTokenLoader(context)
    loaded_apps = app_by_token_loader.batch_load([raw_token])
    fetched_app = loaded_apps[0]

    # then
    # Check that the token was removed from the database
    assert not AppToken.objects.exists()
    # Check that the app was not fetched from the database
    assert fetched_app is None
    # Check that the cache was set only once during given test section
    mocked_cache.set.assert_called_once_with(
        expected_cache_key, (app.id, token_id), 123
    )
    # Check if the token was removed from the cache
    assert mocked_cache.get(expected_cache_key) is None


@patch("saleor.graphql.app.dataloaders.app.cache")
def test_app_by_token_loader_one_of_tokens_in_cache(
    mocked_cache, app, setup_mock_for_cache
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    raw_token = "test_token"
    token, _ = app.tokens.create(
        name="test_token",
        auth_token=raw_token,
    )
    expected_cache_key = create_app_cache_key_from_token(raw_token)
    mocked_cache.set(expected_cache_key, (app.id, token.id), 123)

    raw_token2 = "test_token2"
    token2, _ = app.tokens.create(
        name="test_token2",
        auth_token=raw_token2,
    )
    expected_cache_key2 = create_app_cache_key_from_token(raw_token2)

    # when
    context = SaleorContext()
    app_by_token_loader = AppByTokenLoader(context)
    loaded_apps = app_by_token_loader.batch_load([raw_token, raw_token2])
    fetched_app = loaded_apps[0]
    fetched_app2 = loaded_apps[1]

    # then
    cached_app_id, cached_token_id = mocked_cache.get(expected_cache_key)
    assert token.id == cached_token_id
    assert fetched_app.id == app.id == cached_app_id
    cached_app_id2, cached_token_id2 = mocked_cache.get(expected_cache_key2)
    assert token2.id == cached_token_id2
    assert fetched_app2.id == app.id == cached_app_id2
    # Check that the cache was set once during given test section and second time inside dataloader
    assert mocked_cache.set.call_count == 2


@patch("saleor.graphql.app.dataloaders.app.cache")
def test_app_by_token_loader_tokens_with_same_last_4(
    mocked_cache, app, app_with_token, setup_mock_for_cache
):
    # given
    dummy_cache = {}
    setup_mock_for_cache(dummy_cache, mocked_cache)
    raw_token = "test_token1234"
    token, _ = app.tokens.create(
        name="test_token",
        auth_token=raw_token,
    )
    expected_cache_key = create_app_cache_key_from_token(raw_token)

    app2 = app_with_token
    raw_token2 = "test2_token1234"
    token2, _ = app2.tokens.create(
        name="test_token2",
        auth_token=raw_token2,
    )
    expected_cache_key2 = create_app_cache_key_from_token(raw_token2)

    # when
    context = SaleorContext()
    app_by_token_loader = AppByTokenLoader(context)
    loaded_apps = app_by_token_loader.batch_load([raw_token, raw_token2])
    fetched_app = loaded_apps[0]
    fetched_app2 = loaded_apps[1]

    # then
    assert token.token_last_4 == token2.token_last_4
    cached_app_id, cached_token_id = mocked_cache.get(expected_cache_key)
    assert token.id == cached_token_id
    assert fetched_app.id == app.id == cached_app_id
    cached_app_id2, cached_token_id2 = mocked_cache.get(expected_cache_key2)
    assert token2.id == cached_token_id2
    assert fetched_app2.id == app2.id == cached_app_id2
    # Check that the cache was set once during given test section and second time inside dataloader
    assert mocked_cache.set.call_count == 2
