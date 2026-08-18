from itertools import groupby
from operator import itemgetter

from django.core.management.base import BaseCommand

from ....core.tracing import traced_atomic_transaction
from ...lock_objects import acquire_category_tree_lock
from ...models import Category

MAX_ROWS_SHOWN = 20

BAD_BOUNDS = "invalid lft/rght bounds"
CROSSING = "crossing sibling intervals (descendant leak)"
SPATIAL_MISMATCH = "spatial parent != parent_id (false ancestors)"
TREE_ID_INTEGRITY = "broken tree_id integrity (needs full rebuild)"

COLUMNS = {
    BAD_BOUNDS: "id, lft, rght, tree_id",
    CROSSING: "id_a, id_b, tree_id",
    SPATIAL_MISMATCH: "id, parent_by_fk, parent_by_intervals, tree_id",
    TREE_ID_INTEGRITY: "child_id, tree_id",
}


def collect_problems() -> dict[str, list[tuple]]:
    """Validate the MPTT invariants with one fetch and an interval sweep.

    The last element of every reported row is the tree_id.
    """
    rows = list(
        Category.objects.order_by("tree_id", "lft", "rght").values_list(
            "pk", "parent_id", "tree_id", "lft", "rght"
        )
    )
    problems: dict[str, list[tuple]] = {title: [] for title in COLUMNS}
    tree_id_of = {pk: tree_id for pk, _, tree_id, _, _ in rows}

    for pk, parent_id, tree_id, lft, rght in rows:
        if lft >= rght or (rght - lft) % 2 == 0:
            problems[BAD_BOUNDS].append((pk, lft, rght, tree_id))
        if parent_id is not None and tree_id_of[parent_id] != tree_id:
            problems[TREE_ID_INTEGRITY].append((pk, tree_id))

    for tree_id, tree_rows in groupby(rows, key=itemgetter(2)):
        root_count = 0
        # Open intervals enclosing the current sweep position, outermost first.
        stack: list[tuple[int, int, int]] = []
        for pk, parent_id, _, lft, rght in tree_rows:
            if parent_id is None:
                root_count += 1
            while stack and stack[-1][2] < lft:
                stack.pop()
            problems[CROSSING].extend(
                (open_pk, pk, tree_id)
                for open_pk, open_lft, open_rght in stack
                if open_lft < lft <= open_rght < rght
            )
            spatial_parent = next(
                (
                    open_pk
                    for open_pk, open_lft, open_rght in reversed(stack)
                    if open_lft < lft and open_rght > rght
                ),
                None,
            )
            if spatial_parent != parent_id:
                problems[SPATIAL_MISMATCH].append(
                    (pk, parent_id, spatial_parent, tree_id)
                )
            stack.append((pk, lft, rght))
        if root_count != 1:
            problems[TREE_ID_INTEGRITY].append((None, tree_id))

    return problems


class Command(BaseCommand):
    help = (
        "Detect corrupted MPTT lft/rght data in the Category tree. "
        "Reports only. Pass --fix to rebuild the affected trees."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Rebuild the affected trees from parent_id.",
        )

    def handle(self, *args, **options):
        affected_tree_ids, needs_full_rebuild = self._detect_and_report()

        if not affected_tree_ids:
            self.stdout.write(self.style.SUCCESS("Category MPTT structure is OK."))
            return

        if not options["fix"]:
            self.stdout.write(
                self.style.WARNING(
                    f"Found problems in tree_ids {sorted(affected_tree_ids)}. "
                    "Re-run with --fix to repair them."
                )
            )
            return

        if needs_full_rebuild:
            self.stdout.write(
                "tree_id integrity is broken - running a full "
                "Category.tree.rebuild() ..."
            )
            with traced_atomic_transaction():
                acquire_category_tree_lock()
                Category.tree.rebuild()
        else:
            for tree_id in sorted(affected_tree_ids):
                self.stdout.write(f"Rebuilding tree_id={tree_id} ...")
                with traced_atomic_transaction():
                    acquire_category_tree_lock()
                    Category.tree.partial_rebuild(tree_id)

        remaining_tree_ids, _ = self._detect_and_report(quiet=True)
        if remaining_tree_ids:
            self.stdout.write(
                self.style.ERROR(
                    "Problems remain after rebuild in tree_ids "
                    f"{sorted(remaining_tree_ids)} - parent_id data itself "
                    "may be inconsistent. Inspect it manually."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("All problems fixed - the tree is now consistent.")
            )

    def _detect_and_report(self, quiet: bool = False) -> tuple[set[int], bool]:
        """Run all checks and return affected tree ids and a full-rebuild flag."""
        problems = collect_problems()
        affected_tree_ids = {row[-1] for rows in problems.values() for row in rows}
        needs_full_rebuild = bool(problems[TREE_ID_INTEGRITY])

        if quiet:
            return affected_tree_ids, needs_full_rebuild

        for title, rows in problems.items():
            if not rows:
                continue
            self.stdout.write(self.style.WARNING(f"{title}: {len(rows)} row(s)"))
            self.stdout.write(f"  ({COLUMNS[title]})")
            for row in rows[:MAX_ROWS_SHOWN]:
                self.stdout.write(f"  {row}")
            if len(rows) > MAX_ROWS_SHOWN:
                self.stdout.write(f"  ... and {len(rows) - MAX_ROWS_SHOWN} more")

        return affected_tree_ids, needs_full_rebuild
