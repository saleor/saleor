from django import forms
from django.conf import settings
from django.utils.translation import pgettext_lazy
from django_prices.forms import PriceField

from ...discount.models import Sale, Voucher
from ...shipping.models import ShippingMethodCountry


class SaleForm(forms.ModelForm):

    class Meta:
        model = Sale
        exclude = []

    def clean(self):
        cleaned_data = super(SaleForm, self).clean()
        discount_type = cleaned_data['type']
        value = cleaned_data['value']
        if discount_type == Sale.PERCENTAGE and value > 100:
            self.add_error('value', pgettext_lazy(
                'sale error',
                'Sale cannot exceed 100%'))
        return cleaned_data


class VoucherForm(forms.ModelForm):

    ALL_BASKETS = 'all_baskets'
    DISCOUNT_TYPES = (
        (ALL_BASKETS, 'All baskets'),
    ) + Voucher.TYPE_CHOICES
    type = forms.ChoiceField(
        choices=DISCOUNT_TYPES, initial=ALL_BASKETS,
        label=pgettext_lazy('voucher_form', 'Discount for'))

    class Meta:
        model = Voucher
        exclude = ['limit', 'apply_to', 'product', 'category']

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance')
        if instance and instance.type == Voucher.BASKET_TYPE and instance.limit is None:
            initial['type'] = VoucherForm.ALL_BASKETS
        kwargs['initial'] = initial
        super(VoucherForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(VoucherForm, self).clean()
        if cleaned_data['type'] == VoucherForm.ALL_BASKETS:
            cleaned_data['type'] = Voucher.BASKET_TYPE
        return cleaned_data


class CountriesField(forms.ChoiceField):

    def __init__(self, *args, **kwargs):
        country_codes = ShippingMethodCountry.objects.all()
        country_codes = country_codes.values_list('country_code', flat=True)
        country_codes = country_codes.distinct()
        country_dict = dict(ShippingMethodCountry.COUNTRY_CODE_CHOICES)
        kwargs['choices'] = [
            (country_code, country_dict[country_code]) for country_code in country_codes]
        super(CountriesField, self).__init__(*args, **kwargs)


class ShippingVoucherForm(forms.ModelForm):

    limit = PriceField(
        min_value=0, required=False, currency=settings.DEFAULT_CURRENCY,
        label=pgettext_lazy('voucher_form', 'Shipping cost equal or less than'),
        help_text=pgettext_lazy('voucher_form', 'Any shipping if empty'))
    apply_to = CountriesField(label='Country')

    class Meta:
        model = Voucher
        fields = ['apply_to', 'limit']

    def save(self, commit=True):
        self.instance.category = None
        self.instance.product = None
        return super(ShippingVoucherForm, self).save(commit)


class BasketVoucherForm(forms.ModelForm):

    limit = PriceField(
        min_value=0, required=True, currency = settings.DEFAULT_CURRENCY,
        label=pgettext_lazy('voucher_form', 'Basket total equals or greater than'))

    class Meta:
        model = Voucher
        fields = ['limit']

    def save(self, commit=True):
        self.instance.category = None
        self.instance.limit = None
        self.instance.product = None
        return super(BasketVoucherForm, self).save(commit)


class ProductVoucherForm(forms.ModelForm):

    APPLY_TO_PRODUCT_CHOICES = (
        (Voucher.APPLY_TO_ONE_PRODUCT,
         pgettext_lazy('voucher_form', 'Apply only once')),
        (Voucher.APPLY_TO_ALL_PRODUCTS,
         pgettext_lazy('voucher_form', 'Apply to all matching products')))

    apply_to = forms.ChoiceField(choices=APPLY_TO_PRODUCT_CHOICES, required=False)

    class Meta:
        model = Voucher
        fields = ['product', 'apply_to']

    def save(self, commit=True):
        self.instance.category = None
        self.instance.limit = None
        return super(ProductVoucherForm, self).save(commit)


class CategoryVoucherForm(ProductVoucherForm):

    class Meta:
        model = Voucher
        fields = ['category', 'apply_to']

    def save(self, commit=True):
        self.instance.limit = None
        self.instance.product = None
        return super(CategoryVoucherForm, self).save(commit)
