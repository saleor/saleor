import uuid

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

    ALL_PURCHASES = 'all_purchases'
    DISCOUNT_TYPES = (
        (ALL_PURCHASES, pgettext_lazy('voucher', 'All purchases')),
    ) + Voucher.TYPE_CHOICES
    type = forms.ChoiceField(
        choices=DISCOUNT_TYPES, initial=ALL_PURCHASES,
        label=pgettext_lazy('voucher', 'Discount for'))

    class Meta:
        model = Voucher
        exclude = ['limit', 'apply_to', 'product', 'category']

    def __init__(self, *args, **kwargs):
        initial = kwargs.get('initial', {})
        instance = kwargs.get('instance')
        if (instance and instance.type == Voucher.VALUE_TYPE and
                instance.limit is None):
            initial['type'] = VoucherForm.ALL_PURCHASES
        if instance and instance.id is None and not initial.get('code'):
            initial['code'] = self._generate_code
        kwargs['initial'] = initial
        super(VoucherForm, self).__init__(*args, **kwargs)

    def _generate_code(self):
        while True:
            code = str(uuid.uuid4()).replace('-', '').upper()[:12]
            if not Voucher.objects.filter(code=code).exists():
                return code

    def clean(self):
        cleaned_data = super(VoucherForm, self).clean()
        if cleaned_data['type'] == VoucherForm.ALL_PURCHASES:
            cleaned_data['type'] = Voucher.VALUE_TYPE
        return cleaned_data


class CountriesField(forms.ChoiceField):

    def _get_choices(self):
        country_codes = ShippingMethodCountry.objects.all()
        country_codes = country_codes.values_list('country_code', flat=True)
        country_codes = country_codes.distinct()
        country_dict = dict(ShippingMethodCountry.COUNTRY_CODE_CHOICES)
        return [
            (country_code, country_dict[country_code])
            for country_code in country_codes]

    choices = property(_get_choices, forms.ChoiceField._set_choices)


class ShippingVoucherForm(forms.ModelForm):

    limit = PriceField(
        min_value=0, required=False, currency=settings.DEFAULT_CURRENCY,
        label=pgettext_lazy(
            'voucher', 'Only if shipping cost is less than or equal to'))
    apply_to = CountriesField(label=pgettext_lazy('voucher', 'Country'))

    class Meta:
        model = Voucher
        fields = ['apply_to', 'limit']

    def save(self, commit=True):
        self.instance.category = None
        self.instance.product = None
        return super(ShippingVoucherForm, self).save(commit)


class ValueVoucherForm(forms.ModelForm):

    limit = PriceField(
        min_value=0, required=True, currency=settings.DEFAULT_CURRENCY,
        label=pgettext_lazy(
            'voucher', 'Purchase value greater than or equal to'))

    class Meta:
        model = Voucher
        fields = ['limit']

    def save(self, commit=True):
        self.instance.category = None
        self.instance.limit = None
        self.instance.product = None
        return super(ValueVoucherForm, self).save(commit)


class ProductVoucherForm(forms.ModelForm):

    apply_to = forms.ChoiceField(
        choices=Voucher.APPLY_TO_PRODUCT_CHOICES, required=False)

    class Meta:
        model = Voucher
        fields = ['product', 'apply_to']

    def __init__(self, *args, **kwargs):
        super(ProductVoucherForm, self).__init__(*args, **kwargs)
        self.fields['product'].required = True

    def save(self, commit=True):
        self.instance.category = None
        self.instance.limit = None
        return super(ProductVoucherForm, self).save(commit)


class CategoryVoucherForm(forms.ModelForm):

    apply_to = forms.ChoiceField(
        choices=Voucher.APPLY_TO_PRODUCT_CHOICES, required=False)

    class Meta:
        model = Voucher
        fields = ['category', 'apply_to']

    def __init__(self, *args, **kwargs):
        super(CategoryVoucherForm, self).__init__(*args, **kwargs)
        self.fields['category'].required = True

    def save(self, commit=True):
        self.instance.limit = None
        self.instance.product = None
        return super(CategoryVoucherForm, self).save(commit)
