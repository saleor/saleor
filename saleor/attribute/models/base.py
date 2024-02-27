from typing import TYPE_CHECKING, TypeVar, Union

from django.contrib.postgres.indexes import GinIndex
from django.db import models, transaction
from django.db.models import Case, Exists, F, OrderBy, OuterRef, Q, Value, When

from ...core.db.fields import SanitizedJSONField
from ...core.models import ModelWithExternalReference, ModelWithMetadata, SortableModel
from ...core.units import MeasurementUnits
from ...core.utils.editorjs import clean_editor_js
from ...core.utils.translations import Translation
from ...page.models import Page, PageType
from ...permission.enums import PageTypePermissions, ProductTypePermissions
from ...permission.utils import has_one_of_permissions
from ...product.models import Product, ProductType, ProductVariant
from .. import AttributeEntityType, AttributeInputType, AttributeType

if TYPE_CHECKING:
    from ...account.models import User
    from ...app.models import App


class BaseAssignedAttribute(models.Model):
    # TODO: stop using this class in new code
    # See: https://github.com/saleor/saleor/issues/12881
    class Meta:
        abstract = True

    @property
    def attribute(self):
        return self.assignment.attribute  # type: ignore[attr-defined] # mixin


T = TypeVar("T", bound=models.Model)


class BaseAttributeQuerySet(models.QuerySet[T]):
    def get_public_attributes(self):
        raise NotImplementedError

    def get_visible_to_user(self, requestor: Union["User", "App", None]):
        if has_one_of_permissions(
            requestor,
            [
                PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
                ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,
            ],
        ):
            return self.all()
        return self.get_public_attributes()


class AssociatedAttributeQuerySet(BaseAttributeQuerySet[T]):
    def get_public_attributes(self):
        attributes = Attribute.objects.filter(visible_in_storefront=True)
        return self.filter(Exists(attributes.filter(id=OuterRef("attribute_id"))))


AssociatedAttributeManager = models.Manager.from_queryset(AssociatedAttributeQuerySet)


class AttributeQuerySet(BaseAttributeQuerySet[T]):
    def get_unassigned_product_type_attributes(self, product_type_pk: int):
        return self.product_type_attributes().exclude(
            Q(attributeproduct__product_type_id=product_type_pk)
            | Q(attributevariant__product_type_id=product_type_pk)
        )

    def get_unassigned_page_type_attributes(self, page_type_pk: int):
        return self.page_type_attributes().exclude(
            attributepage__page_type_id=page_type_pk
        )

    def get_assigned_product_type_attributes(self, product_type_pk: int):
        return self.product_type_attributes().filter(
            Q(attributeproduct__product_type_id=product_type_pk)
            | Q(attributevariant__product_type_id=product_type_pk)
        )

    def get_assigned_page_type_attributes(self, product_type_pk: int):
        return self.page_type_attributes().filter(
            Q(attributepage__page_type_id=product_type_pk)
        )

    def get_public_attributes(self):
        return self.filter(visible_in_storefront=True)

    def _get_sorted_m2m_field(self, m2m_field_name: str, asc: bool):
        sort_order_field = F(f"{m2m_field_name}__sort_order")
        id_field = F(f"{m2m_field_name}__id")
        if asc:
            sort_method = sort_order_field.asc(nulls_last=True)
            id_sort: Union[OrderBy, F] = id_field
        else:
            sort_method = sort_order_field.desc(nulls_first=True)
            id_sort = id_field.desc()

        return self.order_by(sort_method, id_sort)

    def product_attributes_sorted(self, asc=True):
        return self._get_sorted_m2m_field("attributeproduct", asc)

    def variant_attributes_sorted(self, asc=True):
        return self._get_sorted_m2m_field("attributevariant", asc)

    def product_type_attributes(self):
        return self.filter(type=AttributeType.PRODUCT_TYPE)

    def page_type_attributes(self):
        return self.filter(type=AttributeType.PAGE_TYPE)


AttributeManager = models.Manager.from_queryset(AttributeQuerySet)


class Attribute(ModelWithMetadata, ModelWithExternalReference):
    slug = models.SlugField(max_length=250, unique=True, allow_unicode=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=AttributeType.CHOICES)

    input_type = models.CharField(
        max_length=50,
        choices=AttributeInputType.CHOICES,
        default=AttributeInputType.DROPDOWN,
    )
    entity_type = models.CharField(
        max_length=50, choices=AttributeEntityType.CHOICES, blank=True, null=True
    )

    product_types = models.ManyToManyField(
        ProductType,
        blank=True,
        related_name="product_attributes",
        through="attribute.AttributeProduct",
        through_fields=("attribute", "product_type"),
    )
    product_variant_types = models.ManyToManyField(
        ProductType,
        blank=True,
        related_name="variant_attributes",
        through="attribute.AttributeVariant",
        through_fields=("attribute", "product_type"),
    )
    page_types = models.ManyToManyField(
        PageType,
        blank=True,
        related_name="page_attributes",
        through="attribute.AttributePage",
        through_fields=("attribute", "page_type"),
    )

    unit = models.CharField(
        max_length=100,
        # MeasurementUnits is constructed programmatically, so mypy can't see its fields
        choices=MeasurementUnits.CHOICES,  # type: ignore[attr-defined]
        blank=True,
        null=True,
    )
    value_required = models.BooleanField(default=False, blank=True)
    is_variant_only = models.BooleanField(default=False, blank=True)
    visible_in_storefront = models.BooleanField(default=True, blank=True)

    filterable_in_storefront = models.BooleanField(default=False, blank=True)
    filterable_in_dashboard = models.BooleanField(default=False, blank=True)

    storefront_search_position = models.IntegerField(default=0, blank=True)
    available_in_grid = models.BooleanField(default=False, blank=True)
    max_sort_order = models.IntegerField(default=None, null=True, blank=True)

    objects = AttributeManager()

    class Meta(ModelWithMetadata.Meta):
        ordering = ("storefront_search_position", "slug")
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            GinIndex(
                name="attribute_gin",
                # `opclasses` and `fields` should be the same length
                fields=["slug", "name", "type", "input_type", "entity_type", "unit"],
                opclasses=["gin_trgm_ops"] * 6,
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def has_values(self) -> bool:
        return self.values.exists()


class AttributeTranslation(Translation):
    attribute = models.ForeignKey(
        Attribute, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)

    class Meta:
        unique_together = (("language_code", "attribute"),)

    def __repr__(self):
        class_ = type(self)
        return f"{class_.__name__}(pk={self.pk!r}, name={self.name!r}, attribute_pk={self.attribute_id!r})"

    def __str__(self) -> str:
        return self.name

    def get_translated_object_id(self):
        return "Attribute", self.attribute_id

    def get_translated_keys(self):
        return {"name": self.name}


class AttributeValueManager(models.Manager):
    def _prepare_query_for_bulk_operation(self, objects_data):
        query_params = models.Q()

        for obj in objects_data:
            defaults = obj.pop("defaults")
            query_params |= models.Q(**obj)
            obj["defaults"] = defaults

        return self.filter(query_params)

    def _is_correct_record(self, record, obj):
        is_correct_record = (
            getattr(record, field_name) == field_value
            for field_name, field_value in obj.items()
            if field_name != "defaults"
        )
        return all(is_correct_record)

    def bulk_get_or_create(self, objects_data):
        # this method mimics django's queryset.get_or_create method on bulk objects
        # instead of performing it one by one
        # https://docs.djangoproject.com/en/5.0/ref/models/querysets/#get-or-create

        results = []
        objects_not_in_db: list[AttributeValue] = []

        # prepare a list that will save order index of attribute values
        objects_enumerated = list(enumerate(objects_data))
        query = self._prepare_query_for_bulk_operation(objects_data)

        # iterate over all records in db and check if they match any of objects data
        for record in query.iterator():
            # iterate over all objects data and check if they match any of records in db
            for index, obj in objects_enumerated:
                if self._is_correct_record(record, obj):
                    # upon finding existing record add it to results
                    results.append((index, record))
                    # remove it from objects list, so it won't be added to new records
                    objects_enumerated.remove((index, obj))

                    break

        # add what is left to the list of new records
        self._add_new_records(objects_enumerated, objects_not_in_db, results)
        # sort results by index as db record order might be different from sort_order
        results.sort()
        results = [obj for index, obj in results]

        if objects_not_in_db:
            # After migrating to Django 4.0 we should use `update_conflicts` instead
            # of `ignore_conflicts`
            # https://docs.djangoproject.com/en/4.1/ref/models/querysets/#bulk-create
            self.bulk_create(
                objects_not_in_db,  # type: ignore[arg-type]
                ignore_conflicts=True,
            )

        return results

    def bulk_update_or_create(self, objects_data):
        # this method mimics django's queryset.update_or_create method on bulk objects
        # https://docs.djangoproject.com/en/5.0/ref/models/querysets/#update-or-create
        results = []
        objects_not_in_db: list[AttributeValue] = []
        objects_to_be_updated = []
        update_fields = set()
        objects_enumerated = list(enumerate(objects_data))
        query = self._prepare_query_for_bulk_operation(objects_data)

        # iterate over all records in db and check if they match any of objects data
        for record in query.iterator():
            # iterate over all objects data and check if they match any of records in db
            for index, obj in objects_enumerated:
                if self._is_correct_record(record, obj):
                    # upon finding a matching record, update it with defaults
                    for key, value in obj["defaults"].items():
                        setattr(record, key, value)
                        update_fields.add(key)

                    # add it to results and objects to be updated
                    results.append((index, record))

                    # add it to objects to be updated, so it can be bulk updated later
                    objects_to_be_updated.append(record)

                    # remove it from objects data, so it won't be added to new records
                    objects_enumerated.remove((index, obj))

                    break

        # add what is left to the list of new records
        self._add_new_records(objects_enumerated, objects_not_in_db, results)

        # sort results by index as db record order might be different from sort_order
        results.sort()
        results = [obj for index, obj in results]

        if objects_not_in_db:
            # After migrating to Django 4.0 we should use `update_conflicts` instead
            # of `ignore_conflicts`
            # https://docs.djangoproject.com/en/4.1/ref/models/querysets/#bulk-create
            self.bulk_create(
                objects_not_in_db,  # type: ignore[arg-type]
                ignore_conflicts=True,
            )

        if objects_to_be_updated:
            self.bulk_update(
                objects_to_be_updated,
                fields=update_fields,  # type: ignore[arg-type]
            )

        return results

    def _add_new_records(self, objects_enumerated, objects_not_in_db, results):
        for index, obj in objects_enumerated:
            # updating object data with defaults as they contain new values
            defaults = obj.pop("defaults")
            obj.update(defaults)

            # add new record to the list of new records, so it can be bulk created later
            record = self.model(**obj)
            objects_not_in_db.append(record)
            results.append((index, record))


class AttributeValue(ModelWithExternalReference):
    name = models.CharField(max_length=250)
    # keeps hex code color value in #RRGGBBAA format
    value = models.CharField(max_length=255, blank=True, default="")
    slug = models.SlugField(max_length=255, allow_unicode=True)
    file_url = models.URLField(null=True, blank=True)
    content_type = models.CharField(max_length=50, null=True, blank=True)
    attribute = models.ForeignKey(
        Attribute, related_name="values", on_delete=models.CASCADE
    )
    rich_text = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    plain_text = models.TextField(
        blank=True,
        null=True,
    )
    boolean = models.BooleanField(blank=True, null=True)
    date_time = models.DateTimeField(blank=True, null=True)

    reference_product = models.ForeignKey(
        Product,
        related_name="references",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    reference_variant = models.ForeignKey(
        ProductVariant,
        related_name="references",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    reference_page = models.ForeignKey(
        Page, related_name="references", on_delete=models.CASCADE, null=True, blank=True
    )
    sort_order = models.IntegerField(editable=False, db_index=True, null=True)

    objects = AttributeValueManager()

    class Meta:
        ordering = ("sort_order", "pk")
        unique_together = ("slug", "attribute")
        indexes = [
            GinIndex(
                name="attribute_search_gin",
                # `opclasses` and `fields` should be the same length
                fields=["name", "slug"],
                opclasses=["gin_trgm_ops"] * 2,
            )
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def input_type(self):
        return self.attribute.input_type

    def get_ordering_queryset(self):
        return self.attribute.values.all()

    @transaction.atomic
    def save(self, *args, **kwargs):
        if self.pk is None or self.sort_order is None:
            self.set_current_sorting_order()

        super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        if self.sort_order is not None:
            qs = self.get_ordering_queryset()
            if qs.filter(sort_order__gt=self.sort_order).update(
                sort_order=F("sort_order") - 1
            ):
                if self.attribute.max_sort_order is None:
                    value = self._calculate_sort_order_value()
                    self.attribute.max_sort_order = max(value - 1, 0)
                    self.attribute.save(update_fields=["max_sort_order"])
                else:
                    Attribute.objects.filter(pk=self.attribute.pk).update(
                        max_sort_order=Case(
                            When(
                                Q(max_sort_order__gt=0),
                                then=F("max_sort_order") - 1,
                            ),
                            default=Value(0),
                        )
                    )

        super().delete(*args, **kwargs)

    def _calculate_sort_order_value(self):
        qs = self.get_ordering_queryset()
        existing_max = SortableModel.get_max_sort_order(qs)
        return -1 if existing_max is None else existing_max

    def _save_new_max_sort_order(self, value):
        self.sort_order = value
        self.attribute.max_sort_order = value
        self.attribute.save(update_fields=["max_sort_order"])

    def set_current_sorting_order(self):
        if self.attribute.max_sort_order is None:
            value = self._calculate_sort_order_value()
            self._save_new_max_sort_order(value + 1)
        else:
            Attribute.objects.filter(pk=self.attribute.pk).update(
                max_sort_order=F("max_sort_order") + 1
            )
            self.attribute.refresh_from_db()
            self.sort_order = self.attribute.max_sort_order


class AttributeValueTranslation(Translation):
    attribute_value = models.ForeignKey(
        AttributeValue, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=250)
    rich_text = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    plain_text = models.TextField(
        blank=True,
        null=True,
    )

    class Meta:
        unique_together = (("language_code", "attribute_value"),)

    def __repr__(self) -> str:
        class_ = type(self)
        return f"{class_.__name__}(pk={self.pk!r}, name={self.name!r}, attribute_value_pk={self.attribute_value_id!r})"

    def __str__(self) -> str:
        return self.name

    def get_translated_object_id(self):
        return "AttributeValue", self.attribute_value_id

    def get_translated_keys(self):
        return {"name": self.name, "rich_text": self.rich_text}

    def get_translation_context(self):
        context = {}
        attribute_value = self.attribute_value
        attribute = attribute_value.attribute
        context["attribute_id"] = attribute.id
        if attribute.input_type in AttributeInputType.TYPES_WITH_UNIQUE_VALUES:
            if attribute.type == AttributeType.PRODUCT_TYPE:
                if assigned_variant_attribute_value := (
                    attribute_value.variantvalueassignment.first()
                ):
                    if variant := assigned_variant_attribute_value.assignment.variant:
                        context["product_variant_id"] = variant.id
                        context["product_id"] = variant.product_id
                elif assigned_product_attribute_value := (
                    attribute_value.productvalueassignment.first()
                ):
                    if product_id := assigned_product_attribute_value.product_id:
                        context["product_id"] = product_id
            elif attribute.type == AttributeType.PAGE_TYPE:
                if assigned_page_attribute_value := (
                    attribute_value.pagevalueassignment.first()
                ):
                    if page := assigned_page_attribute_value.page:
                        context["page_id"] = page.id
                        if page_type_id := page.page_type_id:
                            context["page_type_id"] = page_type_id
        return context
