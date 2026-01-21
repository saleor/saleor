# ruff: noqa: UP031 # printf-style string formatting are more readable for JSON
import random
import re
from copy import deepcopy
from io import StringIO
from unittest import mock

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from ....attribute.models.base import AttributeValue
from ....page.models import Page
from ....product.models import Category, Collection
from ...management.commands.clean_editorjs_fields import MODELS

MODELS_NAMES = [model_cls.__name__ for [model_cls, _field] in MODELS]


def dirty():
    """Return a dirty EditorJS object that needs cleaning."""
    return {
        "blocks": [{"type": "paragraph", "data": {"text": "<img src=x onerror=y>"}}]
    }


def cleaned():
    """Return a cleaned EditorJS object."""
    return {"blocks": [{"type": "paragraph", "data": {"text": '<img src="x">'}}]}


def create_dirty_category(data: None | dict = None) -> Category:
    with mock.patch.object(
        Category.description.field, "_sanitizer_method", side_effect=lambda x: x
    ):
        original_data = deepcopy(data) if data else dirty()
        category = Category(
            name="my-category",
            slug=f"my-category-{random.random()}",
            # Note: we call dirty() again as it will mutate,
            #       original_data thus needs to have a different pointer address
            description=data or dirty(),
        )
        category.save()
        assert (
            category.description == original_data
        ), "The description shouldn't have changed. Was the cleaner mocked properly?"
    return category


def test_handles_errors():
    """Ensure that error caused by invalid data are handled."""

    # Creates an invalid category in order to cause the cleaner to return an error
    data = {"blocks": [{"type": "invalid", "data": {"foo": "bar"}}]}
    category = create_dirty_category(data)
    assert category.description == data

    out_fp = StringIO()
    call_command("clean_editorjs_fields", "--only=Category", stderr=out_fp)

    expected_error = f"Found invalid data for row #{category.pk} (Category)"
    assert expected_error in out_fp.getvalue()

    # Should fail if '--stop-on-error' was provided
    with pytest.raises(CommandError, match=re.escape(expected_error)):
        call_command(
            "clean_editorjs_fields", "--stop-on-error", "--only=Category", stderr=out_fp
        )


def test_detects_dirty_rows():
    """Ensure rows that would be modified are shown in the command's output."""

    category = create_dirty_category()

    out_fp = StringIO()
    call_command("clean_editorjs_fields", "--only=Category", stdout=out_fp)

    # Should have detected a difference
    actual_output = out_fp.getvalue()
    expected_output = (
        """Row #%d would be changed (Category):
\t  {
\t    "blocks": [
\t      {
\t        "data": {
\t-         "text": "<img src=x onerror=y>"
\t?                            ^^^^^^^^^^
\t+         "text": "<img src=\\"x\\">"
\t?                           ++ ^^
\t        },
\t        "type": "paragraph"
\t      }
\t    ]
\t  }"""
        % category.pk
    )
    assert expected_output in actual_output

    # Then, should successfully clean it
    assert "onerror" in category.description["blocks"][0]["data"]["text"]
    call_command("clean_editorjs_fields", "--only=Category", "--apply")
    category.refresh_from_db(fields=["description"])
    assert "onerror" not in category.description["blocks"][0]["data"]["text"]


def test_track_progress():
    """Ensures progress is only reported every N rows and at 100% done."""

    # We create clean categories as we are not trying to check the cleaning behavior
    # it saves a bit of compute time
    Category.objects.bulk_create(
        [
            Category(
                slug=f"category-{i}",
                name=f"category-{i}",
                description={},
                lft=4,
                rght=5,
                tree_id=0,
                level=0,
            )
            for i in range(10)
        ]
    )

    out_fp = StringIO()
    call_command(
        "clean_editorjs_fields",
        "--progress=4",
        "--only=Category",
        stderr=out_fp,
    )

    lines = [
        line
        for line in out_fp.getvalue().splitlines()
        if line.startswith("Progress for")  # Excludes unrelated logs
    ]

    # Should report three times: 2 times because of --progress=4 (every 4 rows)
    # and a 3rd time when it reaches the last row (100%)
    assert lines == [
        "Progress for Category: 40%",
        "Progress for Category: 80%",
        "Progress for Category: 100%",
    ]


@pytest.mark.parametrize(
    ("cmd_args", "expected_models"),
    [
        (
            # Given
            ("--only", "Category", "Collection"),
            # Then, only the following should be scanned
            ("Category", "Collection"),
        ),
        (
            # Given
            ("--exclude", "Category", "Collection"),
            # Then, only the following should be scanned
            list({*MODELS_NAMES} - {"Category", "Collection"}),
        ),
    ],
)
def test_filter_models(cmd_args: tuple[str, ...], expected_models: list[str]):
    """Ensures progress is only reported every N rows and at 100% done."""

    out_fp = StringIO()
    call_command(
        "clean_editorjs_fields",
        "--verbose",
        *cmd_args,
        stderr=out_fp,
    )

    lines = sorted(
        [
            line
            for line in out_fp.getvalue().splitlines()
            if line.startswith("Checking ")  # Excludes unrelated logs
        ]
    )

    expected_lines = sorted([f"Checking {model}..." for model in expected_models])
    assert lines == expected_lines


@pytest.mark.parametrize(
    ("model_cls", "editorjs_field", "create_entry"),
    # This test takes a sample of 3 models:
    # - Page - uses '.content'
    # - Collection - uses '.description'
    # - AttributeValue - uses '.rich_text'
    [
        (
            Page,
            "content",  # => page.content - the EditorJS DB field
            lambda request: Page(
                slug="x",
                title="x",
                page_type=request.getfixturevalue("page_type"),
                content=dirty(),
            ),
        ),
        (
            Collection,
            "description",  # => collection.description - the EditorJS DB field
            lambda _request: Collection(slug="x", name="x", description=dirty()),
        ),
        (
            AttributeValue,
            "rich_text",  # => AttributeValue.description - the EditorJS DB field
            lambda request: AttributeValue(
                slug="x",
                name="x",
                rich_text=dirty(),
                attribute=request.getfixturevalue("rich_text_attribute"),
            ),
        ),
    ],
)
def test_can_clean_all_models(
    request,
    model_cls,
    editorjs_field: str,
    create_entry,
):
    """Ensure rows that would be modified are shown in the command's output."""

    with mock.patch.object(
        # Temporarily disables the cleaner so it doesn't clean the dirty input
        getattr(model_cls, editorjs_field).field,
        "_sanitizer_method",
        side_effect=lambda x: x,
    ):
        entry = create_entry(request)
        entry.save()  # insert into the DB

    # Ensures the field is indeed dirty before we try to clean it
    assert getattr(entry, editorjs_field) == dirty()

    # Start the cleaning
    call_command("clean_editorjs_fields", "--apply", f"--only={model_cls.__name__}")

    # Should have cleaned the model properly
    entry.refresh_from_db(fields=[editorjs_field])
    assert getattr(entry, editorjs_field) == cleaned()
