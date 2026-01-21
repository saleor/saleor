import difflib
import json
import traceback

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import models

from ....attribute.models import AttributeValue, AttributeValueTranslation
from ....discount.models import (
    Promotion,
    PromotionRule,
    PromotionRuleTranslation,
    PromotionTranslation,
)
from ....page.models import Page, PageTranslation
from ....product.models import (
    Category,
    CategoryTranslation,
    Collection,
    CollectionTranslation,
    Product,
    ProductTranslation,
)
from ....shipping.models import ShippingMethod, ShippingMethodTranslation
from ...utils.editorjs import clean_editor_js

# ((<model class>, <field to clean>), ...)
MODELS: tuple[tuple[type[models.Model], str], ...] = (
    # Product module
    (Product, "description"),
    (ProductTranslation, "description"),
    (Collection, "description"),
    (CollectionTranslation, "description"),
    (Category, "description"),
    (CategoryTranslation, "description"),
    # Page module
    (Page, "content"),
    (PageTranslation, "content"),
    # Shipping module
    (ShippingMethod, "description"),
    (ShippingMethodTranslation, "description"),
    # Discount module
    (Promotion, "description"),
    (PromotionTranslation, "description"),
    (PromotionRule, "description"),
    (PromotionRuleTranslation, "description"),
    # Attribute module
    (AttributeValue, "rich_text"),
    (AttributeValueTranslation, "rich_text"),
)


class Command(BaseCommand):
    help = "Runs the Editorjs cleaner against all rows and all models."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            dest="is_dry_run",
            action="store_false",
            help=(
                "When provided, it applies the changes instead of only printing what "
                "it would do (dry run)"
            ),
        )
        parser.add_argument(
            "--stop-on-error",
            action="store_true",
            help=(
                "When provided, the script doesn't continue migrating the data "
                "when invalid data is found (e.g., invalid EditorJS syntax)"
            ),
        )
        parser.add_argument(
            "--progress",
            dest="report_frequency",
            type=int,
            default=1000,
            metavar="N",
            help="Reports the progress (in percents) every N rows processed",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable debug logs and send more details",
        )

        model_names = [model.__name__ for [model, _field] in MODELS]

        model_filter = parser.add_mutually_exclusive_group()
        model_filter.add_argument(
            "--only",
            type=str,
            choices=model_names,
            action="extend",
            nargs="+",
            metavar="MODEL",
            help=(
                "Only clean given models. "
                "See Available Models for the list of allowed values."
            ),
        )
        model_filter.add_argument(
            "--exclude",
            type=str,
            choices=model_names,
            action="extend",
            nargs="+",
            metavar="MODEL",
            help=(
                "Exclude given models from cleaning. "
                "See Available Models for the list of allowed values."
            ),
        )

        parser.epilog = "Available Models: " + ", ".join(model_names)

    def handle(
        self,
        is_dry_run: bool,
        verbose: bool,
        stop_on_error: bool,
        report_frequency: int,
        only: list[str],
        exclude: list[str],
        **_options,
    ):
        self.is_dry_run = is_dry_run
        self.verbose = verbose
        self.stop_on_error = stop_on_error

        # Reports the % progress every N rows (where N is `report_frequency`)
        self.report_frequency = report_frequency

        # Makes django use the default color for stderr, otherwise everything is red
        # despite we don't log an error
        self.stderr.style_func = None # type: ignore[assignment] # None is allowed
        self.differ = difflib.Differ()

        for [model_cls, field] in MODELS:
            # Skip model if --only was provided but this model's name wasn't provided in
            # --only
            if only and model_cls.__name__ not in only:
                if self.verbose:
                    self.stderr.write(f"Skipped: {model_cls.__name__} (not in --only)")
                continue

            if exclude and model_cls.__name__ in exclude:
                if self.verbose:
                    self.stderr.write(
                        f"Skipped: {model_cls.__name__} (not in --exclude)"
                    )
                continue

            self.clean_model(model_cls, field)

        self.stderr.write(
            "To apply the changes, rerun this command with --apply", self.style.NOTICE
        )

    def clean_model(self, cls, field: str):
        table_name = cls.__name__

        if self.is_dry_run is False:
            self.stderr.write(f"Cleaning {table_name} table...")
        elif self.verbose:
            self.stderr.write(f"Checking {table_name}...")

        # Excludes 'null'::jsonb (see https://code.djangoproject.com/ticket/35381)
        qs = (
            cls.objects.all()
            .only("pk", field)
            .filter(~models.Q(**{field: models.Value(None, models.JSONField())}))
        )
        obj_count = qs.count()

        for processed_count, row in enumerate(qs.iterator(chunk_size=100), start=1):
            # Sends a progress update every N rows to prevent the command from looking
            # stuck if there are lot of objects to process
            if (
                processed_count == obj_count
                or (processed_count % self.report_frequency) == 0
            ):
                progress_perc = round(((processed_count) / obj_count) * 100)
                self.stderr.write(f"Progress for {table_name}: {progress_perc}%")

            contents = getattr(row, field)

            # Skip row if type is invalid
            if isinstance(contents, dict) is False:
                self.stderr.write(
                    (
                        f"Expected a dict object but got instead {type(contents)} "
                        f"for table {table_name} with pk={row.pk!r}"
                    ),
                    self.style.NOTICE,
                )
                continue

            # Dump to string before cleaning as the object will be mutated
            before = json.dumps(contents, indent=2)

            # Perform the cleaning

            try:
                cleaned = clean_editor_js(contents)
            except (KeyError, ValidationError, ValueError) as exc:
                msg = f"Found invalid data for row #{row.pk} ({table_name})"
                if self.stop_on_error is True:
                    raise CommandError(msg) from exc

                self.stderr.write(f"ERROR: {msg}", self.style.ERROR)
                self.stderr.write(
                    "\n".join(traceback.format_exception_only(exc)).strip(),
                    self.style.ERROR,
                )
                continue

            after = json.dumps(cleaned, indent=2)

            if after == before:
                continue

            if self.is_dry_run is False:
                row.save(update_fields=[field])
            else:
                self.stdout.write(
                    f"Row #{row.pk} would be changed ({table_name}):",
                    self.style.WARNING,
                )
                for line in self.differ.compare(
                    before.splitlines(),
                    after.splitlines(),
                ):
                    style = None
                    if line:
                        if line[0] == "-":
                            style = self.style.ERROR  # red color for deleted lines
                        elif line[0] == "+":
                            style = self.style.SUCCESS  # green color for added lines
                    self.stdout.write(f"\t{line}", style, ending="\n")
