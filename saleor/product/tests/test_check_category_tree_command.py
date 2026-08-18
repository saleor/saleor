from io import StringIO

from django.core.management import call_command

from ...core.db.locks import AdvisoryLock
from ..models import Category


def _corrupt_sibling_intervals():
    """Give two sibling categories crossing lft/rght intervals (bypassing mptt)."""
    root = Category.objects.create(name="Corrupted root", slug="corrupted-root")
    first = Category.objects.create(name="First", slug="corrupted-first", parent=root)
    second = Category.objects.create(
        name="Second", slug="corrupted-second", parent=root
    )
    Category.objects.filter(pk=root.pk).update(lft=1, rght=8)
    Category.objects.filter(pk=first.pk).update(lft=2, rght=5)
    Category.objects.filter(pk=second.pk).update(lft=3, rght=7)
    return root


def test_reports_corruption_without_fixing(db):
    # given
    root = _corrupt_sibling_intervals()
    stdout = StringIO()

    # when
    call_command("check_category_tree", stdout=stdout)

    # then
    output = stdout.getvalue()
    assert "crossing sibling intervals" in output
    assert f"Found problems in tree_ids [{root.tree_id}]" in output
    # The data was only reported, not repaired.
    first = Category.objects.get(slug="corrupted-first")
    assert (first.lft, first.rght) == (2, 5)


def test_fix_takes_tree_lock_and_repairs(db, assert_advisory_lock_before_tree_write):
    # given
    root = _corrupt_sibling_intervals()

    # when
    with assert_advisory_lock_before_tree_write(
        AdvisoryLock.CATEGORY_TREE, Category._meta.db_table
    ):
        stdout = StringIO()
        call_command("check_category_tree", "--fix", stdout=stdout)

    # then
    assert "All problems fixed" in stdout.getvalue()
    root.refresh_from_db(fields=("lft", "rght"))
    first = Category.objects.get(slug="corrupted-first")
    second = Category.objects.get(slug="corrupted-second")
    # A rebuilt two-child tree spans 1..6 with disjoint sibling intervals.
    assert (root.lft, root.rght) == (1, 6)
    assert {(first.lft, first.rght), (second.lft, second.rght)} == {(2, 3), (4, 5)}
