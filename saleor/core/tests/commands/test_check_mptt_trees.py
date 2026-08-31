from io import StringIO

import pytest
from django.core.management import call_command

from ....core.db.locks import AdvisoryLock
from ....menu.models import MenuItem
from ....product.models import Category


@pytest.fixture
def corrupted_category_tree(db):
    """Give two sibling categories crossing lft/rght intervals (bypassing mptt)."""
    root = Category.objects.create(name="Corrupted root", slug="corrupted-root")
    first = Category.objects.create(name="First", slug="corrupted-first", parent=root)
    second = Category.objects.create(
        name="Second", slug="corrupted-second", parent=root
    )
    Category.objects.filter(pk=root.pk).update(lft=1, rght=8)
    Category.objects.filter(pk=first.pk).update(lft=2, rght=5)
    Category.objects.filter(pk=second.pk).update(lft=3, rght=7)
    return root, first, second


@pytest.fixture
def corrupted_menu_item_tree(menu):
    """Give two sibling menu items crossing lft/rght intervals (bypassing mptt)."""
    root = MenuItem.objects.create(menu=menu, name="Corrupted root")
    first = MenuItem.objects.create(menu=menu, name="First", parent=root)
    second = MenuItem.objects.create(menu=menu, name="Second", parent=root)
    MenuItem.objects.filter(pk=root.pk).update(lft=1, rght=8)
    MenuItem.objects.filter(pk=first.pk).update(lft=2, rght=5)
    MenuItem.objects.filter(pk=second.pk).update(lft=3, rght=7)
    return root, first, second


@pytest.fixture
def category_tree_with_duplicated_root_tree_id(db):
    """Give two root categories the same tree_id (bypassing mptt)."""
    first = Category.objects.create(name="Root A", slug="root-a")
    second = Category.objects.create(name="Root B", slug="root-b")
    Category.objects.filter(pk=second.pk).update(tree_id=first.tree_id, lft=3, rght=4)
    return first, second


@pytest.fixture
def menu_item_tree_with_duplicated_root_tree_id(menu):
    """Give two root menu items the same tree_id (bypassing mptt)."""
    first = MenuItem.objects.create(menu=menu, name="Root A")
    second = MenuItem.objects.create(menu=menu, name="Root B")
    MenuItem.objects.filter(pk=second.pk).update(tree_id=first.tree_id, lft=3, rght=4)
    return first, second


TREE_CASES = [
    (
        "category",
        "corrupted_category_tree",
        Category,
        AdvisoryLock.CATEGORY_TREE,
        MenuItem,
    ),
    (
        "menu_item",
        "corrupted_menu_item_tree",
        MenuItem,
        AdvisoryLock.MENU_ITEM_TREE,
        Category,
    ),
]


@pytest.mark.parametrize(
    ("_case", "tree_fixture", "model", "lock", "other_model"), TREE_CASES
)
def test_reports_corruption_without_fixing(
    request, _case, tree_fixture, model, lock, other_model
):
    # given
    root, first, _second = request.getfixturevalue(tree_fixture)
    stdout = StringIO()

    # when
    call_command("check_mptt_trees", stdout=stdout)

    # then
    output = stdout.getvalue()
    assert f"{model.__name__} crossing sibling intervals" in output
    assert f"Found problems in {model.__name__} tree_ids [{root.tree_id}]" in output
    # The uncorrupted tree was checked too and is healthy.
    assert f"{other_model.__name__} MPTT structure is OK." in output
    # The data was only reported, not repaired.
    first.refresh_from_db(fields=("lft", "rght"))
    assert (first.lft, first.rght) == (2, 5)


@pytest.mark.parametrize(
    ("_case", "tree_fixture", "model", "lock", "other_model"), TREE_CASES
)
def test_fix_takes_tree_lock_and_repairs(
    request,
    _case,
    tree_fixture,
    model,
    lock,
    other_model,
    assert_advisory_lock_before_tree_write,
):
    # given
    root, first, second = request.getfixturevalue(tree_fixture)

    # when
    with assert_advisory_lock_before_tree_write(lock, model._meta.db_table):
        stdout = StringIO()
        call_command("check_mptt_trees", "--fix", stdout=stdout)

    # then
    assert f"All {model.__name__} problems fixed" in stdout.getvalue()
    root.refresh_from_db(fields=("lft", "rght"))
    first.refresh_from_db(fields=("lft", "rght"))
    second.refresh_from_db(fields=("lft", "rght"))
    # A rebuilt two-child tree spans 1..6 with disjoint sibling intervals.
    assert (root.lft, root.rght) == (1, 6)
    assert {(first.lft, first.rght), (second.lft, second.rght)} == {(2, 3), (4, 5)}


@pytest.mark.parametrize(
    ("_case", "tree_fixture", "model"),
    [
        ("category", "category_tree_with_duplicated_root_tree_id", Category),
        ("menu_item", "menu_item_tree_with_duplicated_root_tree_id", MenuItem),
    ],
)
def test_fix_runs_full_rebuild_when_tree_id_integrity_broken(
    request, _case, tree_fixture, model
):
    # given
    first_root, second_root = request.getfixturevalue(tree_fixture)

    # when
    stdout = StringIO()
    call_command("check_mptt_trees", "--fix", stdout=stdout)

    # then
    output = stdout.getvalue()
    assert f"running a full {model.__name__} tree rebuild" in output
    assert f"All {model.__name__} problems fixed" in output
    first_root.refresh_from_db(fields=("lft", "rght", "tree_id"))
    second_root.refresh_from_db(fields=("lft", "rght", "tree_id"))
    # The rebuild reassigns each root its own tree, both childless roots
    # spanning 1..2 again.
    assert first_root.tree_id != second_root.tree_id
    assert (first_root.lft, first_root.rght) == (1, 2)
    assert (second_root.lft, second_root.rght) == (1, 2)
