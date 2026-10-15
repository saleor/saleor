import json
from typing import Any

import graphene
import pytest
from django.db import connections
from django.test.utils import CaptureQueriesContext

from .....permission.enums import ProductPermissions, SitePermissions
from .....product.error_codes import CollectionErrorCode, ProductErrorCode
from .....product.models import (
    Category,
    CategoryTranslation,
    Collection,
    CollectionTranslation,
)
from .....tests.utils import dummy_editorjs
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_translation_payload
from .....webhook.transport.asynchronous.transport import (
    create_deliveries_for_subscriptions,
)
from ....core.enums import LanguageCodeEnum, TranslationErrorCode
from ....tests.utils import get_graphql_content
from ....translations.schema import TranslatableKinds


def serialize_editorjs(value: dict[str, Any] | None) -> str | None:
    return json.dumps(value) if value is not None else None


def deserialize_editorjs(value: str | None) -> dict[str, Any] | None:
    return json.loads(value) if value is not None else None


@pytest.fixture(
    params=[
        {
            "blocks": [
                {"type": "header", "data": {"text": "Summer collection", "level": 2}},
                {
                    "type": "paragraph",
                    "data": {"text": "<b>Rich text</b> — літня колекція."},
                },
                {
                    "type": "list",
                    "data": {"style": "unordered", "items": ["First", "Second"]},
                },
            ]
        },
        {},
        {"blocks": []},
        None,
    ],
    ids=["rich-text", "empty-object", "empty-blocks", "null"],
)
def full_description(request) -> dict[str, Any] | None:
    return request.param


@pytest.fixture(params=["category", "published_collection"])
def catalog_object(request) -> Category | Collection:
    instance = request.getfixturevalue(request.param)
    description = "Existing catalog description."
    instance.description = dummy_editorjs(description)
    update_fields = ["description"]
    if isinstance(instance, Category):
        instance.description_plaintext = description
        update_fields.append("description_plaintext")
    instance.save(update_fields=update_fields)
    return instance


def catalog_mutation(instance: Category | Collection, action: str) -> str:
    name = instance._meta.model_name
    input_type = instance._meta.object_name
    if name == "collection" and action == "Create":
        input_type += "Create"
    id_variable = "$id: ID!," if action == "Update" else ""
    id_argument = "id: $id," if action == "Update" else ""
    return f"""
        mutation ({id_variable} $input: {input_type}Input!) {{
            {name}{action}({id_argument} input: $input) {{
                {name} {{ id fullDescription description }}
                errors {{ field code message }}
            }}
        }}
    """


def test_create_full_description(
    mocker,
    staff_api_client,
    catalog_object,
    permission_manage_products,
    full_description,
):
    # given
    event = mocker.patch(
        f"saleor.plugins.manager.PluginsManager.{catalog_object._meta.model_name}_created"
    )
    description = dummy_editorjs("Existing rich-text description.", True)
    variables = {
        "input": {
            "name": "New catalog page",
            "slug": "new-catalog-page",
            "description": description,
            "fullDescription": serialize_editorjs(full_description),
        }
    }

    # when
    response = staff_api_client.post_graphql(
        catalog_mutation(catalog_object, "Create"),
        variables,
        permissions=[permission_manage_products],
    )

    # then
    name = catalog_object._meta.model_name
    data = get_graphql_content(response)["data"][f"{name}Create"]
    assert data["errors"] == []
    expected = full_description
    assert deserialize_editorjs(data[name]["fullDescription"]) == expected
    assert json.loads(data[name]["description"]) == json.loads(description)
    created = type(catalog_object).objects.get(slug=variables["input"]["slug"])
    assert created.full_description == expected
    event.assert_called_once_with(created)


def test_update_full_description(
    mocker,
    staff_api_client,
    catalog_object,
    permission_manage_products,
    full_description,
):
    # given
    event = mocker.patch(
        f"saleor.plugins.manager.PluginsManager.{catalog_object._meta.model_name}_updated"
    )
    catalog_object.full_description = dummy_editorjs("Previous full description.")
    catalog_object.save(update_fields=["full_description"])
    description = catalog_object.description
    description_plaintext = getattr(catalog_object, "description_plaintext", None)
    variables = {
        "id": graphene.Node.to_global_id(
            catalog_object._meta.object_name, catalog_object.pk
        ),
        "input": {"fullDescription": serialize_editorjs(full_description)},
    }

    # when
    response = staff_api_client.post_graphql(
        catalog_mutation(catalog_object, "Update"),
        variables,
        permissions=[permission_manage_products],
    )

    # then
    name = catalog_object._meta.model_name
    data = get_graphql_content(response)["data"][f"{name}Update"]
    assert data["errors"] == []
    expected = full_description
    assert deserialize_editorjs(data[name]["fullDescription"]) == expected
    catalog_object.refresh_from_db()
    assert catalog_object.full_description == expected
    assert catalog_object.description == description
    if isinstance(catalog_object, Category):
        assert catalog_object.description_plaintext == description_plaintext
    event.assert_called_once_with(catalog_object)


def catalog_translation_mutation(instance: Category | Collection) -> str:
    name = instance._meta.model_name
    return f"""
        mutation ($id: ID!, $input: TranslationInput!, $languageCode: LanguageCodeEnum!) {{
            {name}Translate(id: $id, input: $input, languageCode: $languageCode) {{
                {name} {{
                    fullDescription
                    translation(languageCode: $languageCode) {{
                        name fullDescription description
                    }}
                }}
                errors {{ field code message }}
            }}
        }}
    """


@pytest.fixture
def catalog_translation(
    catalog_object: Category | Collection,
) -> CategoryTranslation | CollectionTranslation:
    return catalog_object.translations.create(
        language_code=LanguageCodeEnum.PL.value,
        name="Original translated name",
        description=dummy_editorjs("Existing translated description."),
        full_description=dummy_editorjs("Previous translated full description."),
    )


def test_create_omitted_full_description(
    staff_api_client, catalog_object, permission_manage_products
):
    # given
    variables = {
        "input": {"name": "No full description", "slug": "no-full-description"}
    }

    # when
    response = staff_api_client.post_graphql(
        catalog_mutation(catalog_object, "Create"),
        variables,
        permissions=[permission_manage_products],
    )

    # then
    name = catalog_object._meta.model_name
    data = get_graphql_content(response)["data"][f"{name}Create"]
    assert data["errors"] == []
    assert data[name]["fullDescription"] is None
    created = type(catalog_object).objects.get(slug=variables["input"]["slug"])
    assert created.full_description is None


def test_update_omitted_full_description(
    staff_api_client, catalog_object, permission_manage_products
):
    # given
    full_description = dummy_editorjs("Preserve this full description.")
    catalog_object.full_description = full_description
    catalog_object.save(update_fields=["full_description"])
    updated_name = "Renamed page"
    variables = {
        "id": graphene.Node.to_global_id(
            catalog_object._meta.object_name, catalog_object.pk
        ),
        "input": {"name": updated_name},
    }

    # when
    response = staff_api_client.post_graphql(
        catalog_mutation(catalog_object, "Update"),
        variables,
        permissions=[permission_manage_products],
    )

    # then
    name = catalog_object._meta.model_name
    data = get_graphql_content(response)["data"][f"{name}Update"]
    assert data["errors"] == []
    assert deserialize_editorjs(data[name]["fullDescription"]) == full_description
    catalog_object.refresh_from_db()
    assert catalog_object.full_description == full_description
    assert catalog_object.name == updated_name


@pytest.mark.parametrize("existing", [False, True])
def test_translate_full_description(
    request,
    mocker,
    staff_api_client,
    catalog_object,
    permission_manage_translations,
    full_description,
    existing,
):
    # given
    if existing:
        request.getfixturevalue("catalog_translation")
    created_event = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_created"
    )
    updated_event = mocker.patch(
        "saleor.plugins.manager.PluginsManager.translations_updated"
    )
    source_description = catalog_object.full_description
    description = dummy_editorjs("Original translated description.", True)
    variables = {
        "id": graphene.Node.to_global_id(
            catalog_object._meta.object_name, catalog_object.pk
        ),
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {
            "fullDescription": serialize_editorjs(full_description),
            "description": description,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        catalog_translation_mutation(catalog_object),
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    name = catalog_object._meta.model_name
    data = get_graphql_content(response)["data"][f"{name}Translate"]
    assert data["errors"] == []
    expected = full_description
    assert deserialize_editorjs(data[name]["fullDescription"]) == source_description
    assert (
        deserialize_editorjs(data[name]["translation"]["fullDescription"]) == expected
    )
    assert json.loads(data[name]["translation"]["description"]) == json.loads(
        description
    )
    translation = catalog_object.translations.get()
    assert translation.full_description == expected
    assert translation.description == json.loads(description)
    catalog_object.refresh_from_db()
    assert catalog_object.full_description == source_description
    if existing:
        updated_event.assert_called_once_with([translation])
        created_event.assert_not_called()
    else:
        created_event.assert_called_once_with([translation])
        updated_event.assert_not_called()
    payload = json.loads(generate_translation_payload(translation))
    assert [item for item in payload["keys"] if item["key"] == "full_description"] == [
        {"key": "full_description", "value": expected}
    ]


@pytest.mark.parametrize("existing", [False, True])
def test_translate_omitted_full_description(
    request, staff_api_client, catalog_object, permission_manage_translations, existing
):
    # given
    expected = None
    if existing:
        translation = request.getfixturevalue("catalog_translation")
        expected = translation.full_description
    updated_name = "Changed translation name"
    variables = {
        "id": graphene.Node.to_global_id(
            catalog_object._meta.object_name, catalog_object.pk
        ),
        "languageCode": LanguageCodeEnum.PL.name,
        "input": {"name": updated_name},
    }

    # when
    response = staff_api_client.post_graphql(
        catalog_translation_mutation(catalog_object),
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    name = catalog_object._meta.model_name
    data = get_graphql_content(response)["data"][f"{name}Translate"]
    assert data["errors"] == []
    assert (
        deserialize_editorjs(data[name]["translation"]["fullDescription"]) == expected
    )
    translation = catalog_object.translations.get()
    assert translation.full_description == expected
    assert translation.name == updated_name


def test_public_query_and_translatable_content(
    api_client,
    staff_api_client,
    catalog_object,
    catalog_translation,
    channel_USD,
    permission_manage_translations,
):
    # given
    full_description = dummy_editorjs("Source full description.")
    catalog_object.full_description = full_description
    catalog_object.save(update_fields=["full_description"])
    name = catalog_object._meta.model_name
    type_name = catalog_object._meta.object_name
    node_id = graphene.Node.to_global_id(type_name, catalog_object.pk)
    channel_argument = (
        f', channel: "{channel_USD.slug}"' if name == "collection" else ""
    )
    public_query = f"""
        query ($id: ID!, $languageCode: LanguageCodeEnum!) {{
            {name}(id: $id {channel_argument}) {{
                fullDescription
                translation(languageCode: $languageCode) {{ fullDescription }}
            }}
        }}
    """
    variables = {"id": node_id, "languageCode": LanguageCodeEnum.PL.name}

    # when
    response = api_client.post_graphql(public_query, variables)

    # then
    data = get_graphql_content(response)["data"][name]
    assert deserialize_editorjs(data["fullDescription"]) == full_description
    assert (
        deserialize_editorjs(data["translation"]["fullDescription"])
        == catalog_translation.full_description
    )

    # when
    query = f"""
        query ($id: ID!, $kind: TranslatableKinds!, $languageCode: LanguageCodeEnum!) {{
            translation(id: $id, kind: $kind) {{
                ... on {type_name}TranslatableContent {{
                    fullDescription
                    translation(languageCode: $languageCode) {{ fullDescription }}
                }}
            }}
        }}
    """
    variables["kind"] = getattr(TranslatableKinds, type_name.upper()).name
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_translations],
    )

    # then
    data = get_graphql_content(response)["data"]["translation"]
    assert deserialize_editorjs(data["fullDescription"]) == full_description
    assert (
        deserialize_editorjs(data["translation"]["fullDescription"])
        == catalog_translation.full_description
    )


@pytest.mark.parametrize("action", ["Create", "Update", "Translate"])
@pytest.mark.parametrize("client_fixture", ["api_client", "staff_api_client"])
def test_full_description_requires_permission(
    request, catalog_object, catalog_translation, action, client_fixture
):
    # given
    client = request.getfixturevalue(client_fixture)
    before_count = type(catalog_object).objects.count()
    source_description = catalog_object.full_description
    translated_description = catalog_translation.full_description
    query = (
        catalog_mutation(catalog_object, action)
        if action != "Translate"
        else catalog_translation_mutation(catalog_object)
    )
    variables = {
        "input": {"fullDescription": dummy_editorjs("Unauthorized change", True)}
    }
    if action == "Create":
        variables["input"]["name"] = "Unauthorized page"
    else:
        variables["id"] = graphene.Node.to_global_id(
            catalog_object._meta.object_name, catalog_object.pk
        )
    if action == "Translate":
        variables["languageCode"] = LanguageCodeEnum.PL.name

    # when
    response = client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert len(content["errors"]) == 1
    permission = (
        SitePermissions.MANAGE_TRANSLATIONS
        if action == "Translate"
        else ProductPermissions.MANAGE_PRODUCTS
    )
    assert content["errors"][0]["message"] == (
        "To access this path, you need one of the following permissions: "
        + permission.name
    )
    assert content["errors"][0]["path"] == [
        f"{catalog_object._meta.model_name}{action}"
    ]
    assert content["errors"][0]["extensions"]["exception"]["code"] == "PermissionDenied"
    catalog_object.refresh_from_db()
    catalog_translation.refresh_from_db()
    assert catalog_object.full_description == source_description
    assert catalog_translation.full_description == translated_description
    assert type(catalog_object).objects.count() == before_count
    assert catalog_object.translations.count() == 1


@pytest.fixture
def catalog_objects(catalog_object):
    model = type(catalog_object)
    objects = [catalog_object]
    objects.extend(
        model.objects.create(name=f"Catalog page {index}", slug=f"catalog-page-{index}")
        for index in range(9)
    )
    translation_model = catalog_object.translations.model
    relation = catalog_object._meta.model_name
    translation_model.objects.bulk_create(
        [
            translation_model(
                **{relation: obj},
                language_code=LanguageCodeEnum.PL.value,
                name=f"Translation {index}",
                full_description=dummy_editorjs(f"Full description {index}"),
            )
            for index, obj in enumerate(objects)
        ]
    )
    return objects


def test_list_full_descriptions_do_not_add_queries(
    staff_api_client,
    catalog_object,
    catalog_objects,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    field = "categories" if isinstance(catalog_object, Category) else "collections"
    query = f"""
        query ($first: Int!, $includeFull: Boolean!, $languageCode: LanguageCodeEnum!) {{
            {field}(first: $first) {{
                edges {{ node {{
                    id
                    fullDescription @include(if: $includeFull)
                    translation(languageCode: $languageCode) {{
                        name
                        fullDescription @include(if: $includeFull)
                    }}
                }} }}
            }}
        }}
    """
    variables = {
        "first": 1,
        "includeFull": False,
        "languageCode": LanguageCodeEnum.PL.name,
    }
    get_graphql_content(staff_api_client.post_graphql(query, variables))
    query_counts = []

    # when
    for first, include_full in [(1, False), (1, True), (len(catalog_objects), True)]:
        variables.update(first=first, includeFull=include_full)
        with (
            CaptureQueriesContext(connections["default"]) as writer_queries,
            CaptureQueriesContext(connections["replica"]) as replica_queries,
        ):
            response = staff_api_client.post_graphql(query, variables)
            data = get_graphql_content(response)["data"][field]
        query_counts.append((len(writer_queries), len(replica_queries)))

        # then
        assert len(data["edges"]) == first
        if include_full:
            assert [edge["node"]["fullDescription"] for edge in data["edges"]] == [
                None
            ] * first
            expected_by_id = {
                graphene.Node.to_global_id(
                    obj._meta.object_name, obj.pk
                ): dummy_editorjs(f"Full description {index}")
                for index, obj in enumerate(catalog_objects)
            }
            for edge in data["edges"]:
                assert (
                    deserialize_editorjs(edge["node"]["translation"]["fullDescription"])
                    == expected_by_id[edge["node"]["id"]]
                )
    assert query_counts[1:] == [query_counts[0], query_counts[0]]


@pytest.mark.parametrize(
    ("event_type", "event_name"),
    [
        (WebhookEventAsyncType.TRANSLATION_CREATED, "TranslationCreated"),
        (WebhookEventAsyncType.TRANSLATION_UPDATED, "TranslationUpdated"),
    ],
)
def test_translation_subscription_full_description(
    catalog_object,
    catalog_translation,
    subscription_webhook,
    event_type,
    event_name,
):
    # given
    type_name = catalog_object._meta.object_name
    query = f"""
        subscription {{ event {{ ... on {event_name} {{
            translation {{ ... on {type_name}Translation {{
                fullDescription
                translatableContent {{ fullDescription }}
            }} }}
        }} }} }}
    """
    webhook = subscription_webhook(query, event_type)

    # when
    deliveries = create_deliveries_for_subscriptions(
        event_type, catalog_translation, [webhook]
    )

    # then
    assert len(deliveries) == 1
    assert deliveries[0].webhook == webhook
    payload = json.loads(deliveries[0].payload.get_payload())
    assert (
        deserialize_editorjs(payload["translation"]["fullDescription"])
        == catalog_translation.full_description
    )
    assert (
        deserialize_editorjs(
            payload["translation"]["translatableContent"]["fullDescription"]
        )
        == catalog_object.full_description
    )


@pytest.mark.parametrize(
    "invalid_description",
    [
        "Plain text instead of an Editor.js document",
        ["Not an Editor.js document"],
        {"blocks": [{"type": "unsupported", "data": {}}]},
    ],
    ids=["plain-text", "array", "unsupported-block"],
)
@pytest.mark.parametrize(
    ("action", "existing_translation"),
    [("Create", False), ("Update", False), ("Translate", False), ("Translate", True)],
)
def test_invalid_full_description_has_field_error(
    request,
    mocker,
    staff_api_client,
    catalog_object,
    permission_manage_products,
    permission_manage_translations,
    invalid_description,
    action,
    existing_translation,
):
    # given
    name = catalog_object._meta.model_name
    translation = (
        request.getfixturevalue("catalog_translation") if existing_translation else None
    )
    before_count = type(catalog_object).objects.count()
    original_name = catalog_object.name
    original_description = catalog_object.description
    original_full_description = catalog_object.full_description
    original_translation = (
        (translation.name, translation.description, translation.full_description)
        if translation
        else None
    )
    if action == "Translate":
        event_name = (
            "translations_updated" if existing_translation else "translations_created"
        )
    else:
        event_name = f"{name}_{'created' if action == 'Create' else 'updated'}"
    event = mocker.patch(f"saleor.plugins.manager.PluginsManager.{event_name}")
    query = (
        catalog_translation_mutation(catalog_object)
        if action == "Translate"
        else catalog_mutation(catalog_object, action)
    )
    variables = {
        "input": {
            "name": "Rejected name",
            "fullDescription": json.dumps(invalid_description),
        }
    }
    if action != "Create":
        variables["id"] = graphene.Node.to_global_id(
            catalog_object._meta.object_name, catalog_object.pk
        )
    if action == "Translate":
        variables["languageCode"] = LanguageCodeEnum.PL.name
    permission = (
        permission_manage_translations
        if action == "Translate"
        else permission_manage_products
    )

    # when
    response = staff_api_client.post_graphql(query, variables, permissions=[permission])

    # then
    data = get_graphql_content(response)["data"][f"{name}{action}"]
    error_code = (
        TranslationErrorCode
        if action == "Translate"
        else ProductErrorCode
        if isinstance(catalog_object, Category)
        else CollectionErrorCode
    )
    assert data[name] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": "fullDescription",
        "code": error_code.INVALID.name,
        "message": "Invalid EditorJS input",
    }
    assert type(catalog_object).objects.count() == before_count
    catalog_object.refresh_from_db()
    assert catalog_object.name == original_name
    assert catalog_object.description == original_description
    assert catalog_object.full_description == original_full_description
    assert catalog_object.translations.count() == int(existing_translation)
    if translation:
        translation.refresh_from_db()
        assert (
            translation.name,
            translation.description,
            translation.full_description,
        ) == original_translation
    event.assert_not_called()


@pytest.mark.parametrize("action", ["Create", "Update", "Translate"])
def test_full_description_is_sanitized_in_storage_and_response(
    request,
    staff_api_client,
    catalog_object,
    permission_manage_products,
    permission_manage_translations,
    action,
):
    # given
    name = catalog_object._meta.model_name
    translation = (
        request.getfixturevalue("catalog_translation")
        if action == "Translate"
        else None
    )
    original_description = (
        translation.description if translation else catalog_object.description
    )
    dirty_description = {
        "blocks": [
            {
                "type": "paragraph",
                "data": {"text": "<b>Summer</b><img src=x onerror=alert(1)>"},
            }
        ]
    }
    expected_description = {
        "blocks": [
            {"type": "paragraph", "data": {"text": '<b>Summer</b><img src="x">'}}
        ]
    }
    variables = {"input": {"fullDescription": json.dumps(dirty_description)}}
    query = (
        catalog_translation_mutation(catalog_object)
        if action == "Translate"
        else catalog_mutation(catalog_object, action)
    )
    if action == "Create":
        variables["input"].update(name="Sanitized page", slug="sanitized-page")
    else:
        variables["id"] = graphene.Node.to_global_id(
            catalog_object._meta.object_name, catalog_object.pk
        )
    if action == "Translate":
        variables["languageCode"] = LanguageCodeEnum.PL.name
    permission = (
        permission_manage_translations
        if action == "Translate"
        else permission_manage_products
    )

    # when
    response = staff_api_client.post_graphql(query, variables, permissions=[permission])

    # then
    data = get_graphql_content(response)["data"][f"{name}{action}"]
    assert data["errors"] == []
    result = data[name]["translation"] if translation else data[name]
    assert json.loads(result["fullDescription"]) == expected_description
    if action == "Create":
        instance = type(catalog_object).objects.get(slug=variables["input"]["slug"])
    else:
        instance = translation if translation else catalog_object
        instance.refresh_from_db()
        assert instance.description == original_description
        assert json.loads(result["description"]) == original_description
    assert instance.full_description == expected_description
