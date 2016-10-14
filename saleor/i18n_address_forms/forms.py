from django_countries.data import COUNTRIES
from django.utils.translation import ugettext_lazy as _

from ..userprofile.models import Address
from ..userprofile.forms import AddressForm
import i18naddress

COUNTRY_FORMS = {}


class CountryAwareAddressForm(AddressForm):

    I18N_MAPPING = (
        ('name', ['first_name', 'last_name']),
        ('street_address', ['street_address']),
        ('city_area', ['city_area']),
        ('country_area', ['country_area']),
        ('company_name', ['company_name']),
        ('postal_code', ['postal_code']),
        ('city', ['city']),
        ('sorting_code', ['sorting_code']),
        ('country_code', ['country_code'])
    )

    class Meta:
        model = Address
        exclude = []

    def add_field_errors(self, errors):
        field_mapping = dict(self.I18N_MAPPING)
        for field_name, error_code in errors.items():
            local_fields = field_mapping[field_name]
            for field in local_fields:
                try:
                    error_msg = self.fields[field].error_messages[error_code]
                except KeyError:
                    error_msg = _('This value is invalid for selected country')
                self.add_error(field, error_msg)

    def validate_address(self, data):
        try:
            data['country_code'] = data['country']
            i18naddress.normalize_address(data)
        except i18naddress.InvalidAddress as exc:
            self.add_field_errors(exc.errors)

    def clean(self):
        data = super(AddressForm, self).clean()
        self.validate_address(data)
        return data


def get_form_18n_lines(form_instance):
    country_code = form_instance.i18n_country_code
    fields_order = i18naddress.get_fields_order({'country_code': country_code})
    field_mapping = dict(form_instance.I18N_MAPPING)

    def _convert_to_bound_fields(form, i18n_field_names):
        bound_fields = []
        for field_name in i18n_field_names:
            local_fields = field_mapping[field_name]
            for local_name in local_fields:
                local_field = form_instance.fields[local_name]
                bound_field = local_field.get_bound_field(form, local_name)
                bound_fields.append(bound_field)
        return bound_fields

    if fields_order:
        return [_convert_to_bound_fields(form_instance, line)
                for line in fields_order]


def update_base_fields(form_class, i18n_rules):
    labels_map = {
        'country_area': r'%(country_area_type)s',
        'postal_code': r'%(postal_code_type)s code',
        'city_area': r'%(city_area_type)s'
    }
    for field_name in labels_map:
        field = form_class.base_fields[field_name]
        new_label = labels_map[field_name] % i18n_rules.__dict__
        field.label = new_label.title()


def construct_address_form(country_code, i18n_rules):
    class_name = 'AddressForm%s' % country_code
    base_class = CountryAwareAddressForm
    form_kwargs = {
        'Meta': type(str('Meta'), (base_class.Meta, object), {}),
        'formfield_callback': None,}
    klass = type(base_class)(str(class_name), (base_class,), form_kwargs)
    update_base_fields(klass, i18n_rules)
    klass.i18n_country_code = country_code
    klass.i18n_fields_order = property(get_form_18n_lines)
    return klass

for country in COUNTRIES.keys():
    try:
        country_rules = i18naddress.get_validation_rules({'country_code': country})
    except ValueError:
        continue

    COUNTRY_FORMS[country] = construct_address_form(country, country_rules)
