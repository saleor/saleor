from django import forms
from django.conf import settings
from django.urls import reverse_lazy
from django.utils.translation import pgettext_lazy
from django_countries import countries
from django_prices.forms import MoneyField
from mptt.forms import TreeNodeMultipleChoiceField

from ...core.utils.taxes import ZERO_MONEY
from ...discount import DiscountValueType
from ...discount.models import Sale, Voucher
from ...discount.utils import generate_voucher_code
from ...product.models import Category, Product
from ..forms import AjaxSelect2MultipleChoiceField

MinAmountSpent = MoneyField(
    min_value=ZERO_MONEY, required=False,
    currency=settings.DEFAULT_CURRENCY,
    label=pgettext_lazy(
        'Lowest value for order to be able to use the voucher',
        'Apply only if the purchase value is greater than or equal to'))


class SaleForm(forms.ModelForm):
    products = AjaxSelect2MultipleChoiceField(
        queryset=Product.objects.all(),
        fetch_data_url=reverse_lazy('dashboard:ajax-products'),
        required=False,
        label=pgettext_lazy('Discounted products', 'Discounted products'))

    class Meta:
        model = Sale
        exclude = []
        labels = {
            'name': pgettext_lazy(
                'Sale name',
                'Name'),
            'type': pgettext_lazy(
                'Discount type',
                'Fixed or percentage'),
            'start_date': pgettext_lazy(
                'Sale date restrictions',
                'Start date'),
            'end_date': pgettext_lazy(
                'Sale date restrictions',
                'End date'),
            'value': pgettext_lazy(
                'Percentage or fixed amount value',
                'Value'),
            'categories': pgettext_lazy(
                'Discounted categories',
                'Discounted categories'),
            'collections': pgettext_lazy(
                'Discounted collections',
                'Discounted collections')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['products'].set_initial(self.instance.products.all())

    def clean(self):
        cleaned_data = super().clean()
        discount_type = cleaned_data['type']
        value = cleaned_data['value']
        if discount_type == DiscountValueType.PERCENTAGE and value > 100:
            self.add_error('value', pgettext_lazy(
                'Sale (discount) error',
                'Sale cannot exceed 100%'))
        products = cleaned_data.get('products')
        categories = cleaned_data.get('categories')
        collections = cleaned_data.get('collections')
        if not any([products, categories, collections]):
            raise forms.ValidationError(pgettext_lazy(
                'Sale (discount) error',
                'A single sale must point to at least one product, collection'
                'and/or category.'))
        return cleaned_data


class VoucherForm(forms.ModelForm):

    class Meta:
        model = Voucher
        exclude = [
            'min_amount_spent', 'countries', 'products', 'collections',
            'categories', 'used']
        labels = {
            'type': pgettext_lazy(
                'Discount type',
                'Discount type'),
            'name': pgettext_lazy(
                'Item name',
                'Name'),
            'code': pgettext_lazy(
                'Coupon code',
                'Code'),
            'usage_limit': pgettext_lazy(
                'Usage limit',
                'Usage limit'),
            'start_date': pgettext_lazy(
                'Voucher date restrictions',
                'Start date'),
            'end_date': pgettext_lazy(
                'Voucher date restrictions',
                'End date'),
            'discount_value_type': pgettext_lazy(
                'Discount type of the voucher',
                'Discount type'),
            'discount_value': pgettext_lazy(
                'Discount value of the voucher',
                'Discount value')}

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance')
        if instance and instance.id is None and not initial.get('code'):
            initial['code'] = generate_voucher_code()
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)


class ShippingVoucherForm(forms.ModelForm):
    min_amount_spent = MinAmountSpent
    countries = forms.MultipleChoiceField(
        choices=countries,
        required=False,
        label=pgettext_lazy(
            'Text above the dropdown of countries',
            'Limit countries that voucher should apply to'))

    class Meta:
        model = Voucher
        fields = ['countries', 'min_amount_spent']


class ValueVoucherForm(forms.ModelForm):
    min_amount_spent = MinAmountSpent

    class Meta:
        model = Voucher
        fields = ['min_amount_spent']

    def save(self, commit=True):
        self.instance.category = None
        self.instance.countries = []
        self.instance.product = None
        return super().save(commit)


class CommonVoucherForm(forms.ModelForm):
    use_required_attribute = False
    min_amount_spent = MinAmountSpent
    apply_once_per_order = forms.BooleanField(
        required=False,
        label=pgettext_lazy(
            'Field label, apply discount value only once per order',
            'Only apply once per order'),
        help_text=pgettext_lazy(
            'Help text of checkbox for applying discount only once per order',
            'If unchecked, discount value will be taken '
            'off each suitable item in an order.'))


class ProductVoucherForm(CommonVoucherForm):
    products = AjaxSelect2MultipleChoiceField(
        queryset=Product.objects.all(),
        fetch_data_url=reverse_lazy('dashboard:ajax-products'),
        required=True,
        label=pgettext_lazy('Product', 'Products'))

    class Meta:
        model = Voucher
        fields = ['products', 'apply_once_per_order']


class CollectionVoucherForm(CommonVoucherForm):

    class Meta:
        model = Voucher
        fields = ['collections', 'apply_once_per_order']
        labels = {
            'collections': pgettext_lazy(
                'Collections', 'Collections')}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['collections'].required = True


class CategoryVoucherForm(CommonVoucherForm):
    categories = TreeNodeMultipleChoiceField(
        queryset=Category.objects.all(),
        required=True,
        label=pgettext_lazy('Categories', 'Categories'))

    class Meta:
        model = Voucher
        fields = ['categories', 'apply_once_per_order']
