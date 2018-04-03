import bleach
from django import forms
from django.conf import settings
from django.db.models import Count
from django.forms.models import ModelChoiceIterator
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.encoding import smart_text
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from mptt.forms import TreeNodeChoiceField

from . import ProductBulkAction
from ...product.models import (
    AttributeChoiceValue, Category, Collection, Product, ProductAttribute,
    ProductImage, ProductType, ProductVariant, Stock, StockLocation,
    VariantImage)
from ...product.thumbnails import create_product_thumbnails
from ..forms import ModelChoiceOrCreationField, OrderedModelMultipleChoiceField
from ..seo.fields import SeoDescriptionField, SeoTitleField
from ..seo.utils import prepare_seo_description
from ..widgets import RichTextEditorWidget
from .widgets import ImagePreviewWidget


class RichTextField(forms.CharField):
    """A field for rich text editor, providing backend sanitization."""

    widget = RichTextEditorWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.help_text = pgettext_lazy(
            'Help text in rich-text editor field',
            'Select text to enable text-formatting tools.')

    def to_python(self, value):
        tags = settings.ALLOWED_TAGS or bleach.ALLOWED_TAGS
        attributes = settings.ALLOWED_ATTRIBUTES or bleach.ALLOWED_ATTRIBUTES
        styles = settings.ALLOWED_STYLES or bleach.ALLOWED_STYLES
        value = super().to_python(value)
        value = bleach.clean(
            value, tags=tags, attributes=attributes, styles=styles)
        return value


class ProductTypeSelectorForm(forms.Form):
    """Form that allows selecting product type."""

    product_type = forms.ModelChoiceField(
        queryset=ProductType.objects.all(),
        label=pgettext_lazy('Product type form label', 'Product type'),
        widget=forms.RadioSelect, empty_label=None)


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        exclude = ['quantity_allocated', 'variant']
        labels = {
            'location': pgettext_lazy(
                'Stock location', 'Location'),
            'quantity': pgettext_lazy(
                'Integer number', 'Quantity'),
            'cost_price': pgettext_lazy(
                'Currency amount', 'Cost price')}

    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop('variant')
        super().__init__(*args, **kwargs)

    def clean_location(self):
        location = self.cleaned_data['location']
        if (
                not self.instance.pk and
                self.variant.stock.filter(location=location).exists()):
            self.add_error(
                'location',
                pgettext_lazy(
                    'stock form error',
                    'Stock item for this location and variant already exists'))
        return location

    def save(self, commit=True):
        self.instance.variant = self.variant
        return super().save(commit)


class ProductTypeForm(forms.ModelForm):
    class Meta:
        model = ProductType
        exclude = []
        labels = {
            'name': pgettext_lazy(
                'Item name',
                'Name'),
            'has_variants': pgettext_lazy(
                'Enable variants',
                'Enable variants'),
            'variant_attributes': pgettext_lazy(
                'Product type attributes',
                'Attributes specific to each variant'),
            'product_attributes': pgettext_lazy(
                'Product type attributes',
                'Attributes common to all variants'),
            'is_shipping_required': pgettext_lazy(
                'Shipping toggle',
                'Require shipping')}

    def clean(self):
        data = super().clean()
        has_variants = self.cleaned_data['has_variants']
        product_attr = set(self.cleaned_data['product_attributes'])
        variant_attr = set(self.cleaned_data['variant_attributes'])
        if not has_variants and variant_attr:
            msg = pgettext_lazy(
                'Product type form error',
                'Product variants are disabled.')
            self.add_error('variant_attributes', msg)
        if product_attr & variant_attr:
            msg = pgettext_lazy(
                'Product type form error',
                'A single attribute can\'t belong to both a product '
                'and its variant.')
            self.add_error('variant_attributes', msg)

        if self.instance.pk:
            variants_changed = (
                self.fields['has_variants'].initial != has_variants)
            if variants_changed:
                query = self.instance.products.all()
                query = query.annotate(variants_counter=Count('variants'))
                query = query.filter(variants_counter__gt=1)
                if query.exists():
                    msg = pgettext_lazy(
                        'Product type form error',
                        'Some products of this type have more than '
                        'one variant.')
                    self.add_error('has_variants', msg)
        return data


class AttributesMixin(object):
    """Form mixin that dynamically adds attribute fields."""

    available_attributes = ProductAttribute.objects.none()

    # Name of a field in self.instance that hold attributes HStore
    model_attributes_field = None

    def __init__(self, *args, **kwargs):
        if not self.model_attributes_field:
            raise Exception(
                'model_attributes_field must be set in subclasses of '
                'AttributesMixin.')

    def prepare_fields_for_attributes(self):
        initial_attrs = getattr(self.instance, self.model_attributes_field)
        for attribute in self.available_attributes:
            field_defaults = {
                'label': attribute.name, 'required': False,
                'initial': initial_attrs.get(str(attribute.pk))}
            if attribute.has_values():
                field = ModelChoiceOrCreationField(
                    queryset=attribute.values.all(), **field_defaults)
            else:
                field = forms.CharField(**field_defaults)
            self.fields[attribute.get_formfield_name()] = field

    def iter_attribute_fields(self):
        for attr in self.available_attributes:
            yield self[attr.get_formfield_name()]

    def get_saved_attributes(self):
        attributes = {}
        for attr in self.available_attributes:
            value = self.cleaned_data.pop(attr.get_formfield_name())
            if value:
                # if the passed attribute value is a string,
                # create the attribute value.
                if not isinstance(value, AttributeChoiceValue):
                    value = AttributeChoiceValue(
                        attribute_id=attr.pk, name=value, slug=slugify(value))
                    value.save()
                attributes[smart_text(attr.pk)] = smart_text(value.pk)
        return attributes


class ProductForm(forms.ModelForm, AttributesMixin):
    class Meta:
        model = Product
        exclude = ['attributes', 'product_type', 'updated_at']
        labels = {
            'name': pgettext_lazy('Item name', 'Name'),
            'description': pgettext_lazy('Description', 'Description'),
            'seo_description': pgettext_lazy(
                'A SEO friendly description', 'SEO Friendly Description'),
            'category': pgettext_lazy('Category', 'Category'),
            'price': pgettext_lazy('Currency amount', 'Price'),
            'available_on': pgettext_lazy(
                'Availability date', 'Publish product on'),
            'is_published': pgettext_lazy(
                'Product published toggle', 'Published'),
            'is_featured': pgettext_lazy(
                'Featured product toggle',
                'Feature this product on homepage'),
            'collections': pgettext_lazy(
                'Add to collection select', 'Collections')}

    category = TreeNodeChoiceField(queryset=Category.objects.all())
    collections = forms.ModelMultipleChoiceField(
        required=False, queryset=Collection.objects.all())
    description = RichTextField()

    model_attributes_field = 'attributes'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        product_type = self.instance.product_type
        self.available_attributes = (
            product_type.product_attributes.prefetch_related('values').all())
        self.prepare_fields_for_attributes()
        self.fields['collections'].initial = Collection.objects.filter(
            products__name=self.instance)
        self.fields['seo_description'] = SeoDescriptionField(
            extra_attrs={
                'data-bind': self['description'].auto_id,
                'data-materialize': self['description'].html_name})
        self.fields['seo_title'] = SeoTitleField(
            extra_attrs={'data-bind': self['name'].auto_id})

    def clean_seo_description(self):
        seo_description = prepare_seo_description(
            seo_description=self.cleaned_data['seo_description'],
            html_description=self.data['description'],
            max_length=self.fields['seo_description'].max_length)
        return seo_description

    def save(self, commit=True):
        attributes = self.get_saved_attributes()
        self.instance.attributes = attributes
        instance = super().save()
        instance.collections.clear()
        for collection in self.cleaned_data['collections']:
            instance.collections.add(collection)
        return instance


class ProductVariantForm(forms.ModelForm, AttributesMixin):
    model_attributes_field = 'attributes'

    class Meta:
        model = ProductVariant
        exclude = ['attributes', 'product', 'images']
        labels = {
            'sku': pgettext_lazy('SKU', 'SKU'),
            'price_override': pgettext_lazy(
                'Override price', 'Override price'),
            'name': pgettext_lazy('Product variant name', 'Name')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.product.pk:
            self.fields['price_override'].widget.attrs[
                'placeholder'] = self.instance.product.price.amount
            self.available_attributes = (
                self.instance.product.product_type.variant_attributes.all()
                .prefetch_related('values'))
            self.prepare_fields_for_attributes()

    def save(self, commit=True):
        attributes = self.get_saved_attributes()
        self.instance.attributes = attributes
        return super().save(commit=commit)


class CachingModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        if self.field.empty_label is not None:
            yield ('', self.field.empty_label)
        for obj in self.queryset:
            yield self.choice(obj)


class CachingModelChoiceField(forms.ModelChoiceField):
    def _get_choices(self):
        if hasattr(self, '_choices'):
            return self._choices
        return CachingModelChoiceIterator(self)
    choices = property(_get_choices, forms.ChoiceField._set_choices)


class VariantBulkDeleteForm(forms.Form):
    items = forms.ModelMultipleChoiceField(queryset=ProductVariant.objects)

    def delete(self):
        items = ProductVariant.objects.filter(
            pk__in=self.cleaned_data['items'])
        items.delete()


class StockBulkDeleteForm(forms.Form):
    items = forms.ModelMultipleChoiceField(queryset=Stock.objects)

    def delete(self):
        items = Stock.objects.filter(pk__in=self.cleaned_data['items'])
        items.delete()


class ProductImageForm(forms.ModelForm):
    use_required_attribute = False
    variants = forms.ModelMultipleChoiceField(
        queryset=ProductVariant.objects.none(),
        widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = ProductImage
        exclude = ('product', 'order')
        labels = {
            'image': pgettext_lazy('Product image', 'Image'),
            'alt': pgettext_lazy(
                'Description', 'Description')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.image:
            self.fields['image'].widget = ImagePreviewWidget()

    def save(self, commit=True):
        image = super().save(commit=commit)
        create_product_thumbnails.delay(image.pk)
        return image


class VariantImagesSelectForm(forms.Form):
    images = forms.ModelMultipleChoiceField(
        queryset=VariantImage.objects.none(),
        widget=CheckboxSelectMultiple,
        required=False)

    def __init__(self, *args, **kwargs):
        self.variant = kwargs.pop('variant')
        super().__init__(*args, **kwargs)
        self.fields['images'].queryset = self.variant.product.images.all()
        self.fields['images'].initial = self.variant.images.all()

    def save(self):
        images = []
        self.variant.images.clear()
        for image in self.cleaned_data['images']:
            images.append(VariantImage(variant=self.variant, image=image))
        VariantImage.objects.bulk_create(images)


class ProductAttributeForm(forms.ModelForm):
    class Meta:
        model = ProductAttribute
        exclude = []
        labels = {
            'name': pgettext_lazy(
                'Product display name', 'Display name'),
            'slug': pgettext_lazy(
                'Product internal name', 'Internal name')}


class StockLocationForm(forms.ModelForm):
    class Meta:
        model = StockLocation
        exclude = []
        labels = {
            'name': pgettext_lazy(
                'Item name', 'Name')}


class AttributeChoiceValueForm(forms.ModelForm):
    class Meta:
        model = AttributeChoiceValue
        fields = ['attribute', 'name', 'color']
        widgets = {'attribute': forms.widgets.HiddenInput()}
        labels = {
            'name': pgettext_lazy(
                'Item name', 'Name'),
            'color': pgettext_lazy(
                'Color', 'Color')}

    def save(self, commit=True):
        self.instance.slug = slugify(self.instance.name)
        return super().save(commit=commit)


class ReorderProductImagesForm(forms.ModelForm):
    ordered_images = OrderedModelMultipleChoiceField(
        queryset=ProductImage.objects.none())

    class Meta:
        model = Product
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['ordered_images'].queryset = self.instance.images.all()

    def save(self):
        for order, image in enumerate(self.cleaned_data['ordered_images']):
            image.order = order
            image.save()
        return self.instance


class UploadImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ('image', )
        labels = {
            'image': pgettext_lazy('Product image', 'Image')}

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product')
        super().__init__(*args, **kwargs)
        self.instance.product = product

    def save(self, commit=True):
        image = super().save(commit=commit)
        create_product_thumbnails.delay(image.pk)
        return image


class ProductBulkUpdate(forms.Form):
    """Performs one selected bulk action on all selected products."""

    action = forms.ChoiceField(choices=ProductBulkAction.CHOICES)
    products = forms.ModelMultipleChoiceField(queryset=Product.objects.all())

    def save(self):
        action = self.cleaned_data['action']
        if action == ProductBulkAction.PUBLISH:
            self._publish_products()
        elif action == ProductBulkAction.UNPUBLISH:
            self._unpublish_products()

    def _publish_products(self):
        self.cleaned_data['products'].update(is_published=True)

    def _unpublish_products(self):
        self.cleaned_data['products'].update(is_published=False)
