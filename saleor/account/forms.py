from phonenumbers.phonenumberutil import country_code_for_region

from .i18n import AddressMetaForm, get_address_form_class


def get_address_form(
    data, country_code, initial=None, instance=None, enable_normalization=True, **kwargs
):
    country_form = AddressMetaForm(data, initial=initial)
    preview = False
    if country_form.is_valid():
        country_code = country_form.cleaned_data["country"]
        preview = country_form.cleaned_data["preview"]

    if initial is None and country_code:
        initial = {}
    if country_code:
        initial["phone"] = "+{}".format(country_code_for_region(country_code))

    address_form_class = get_address_form_class(country_code)

    if not preview and instance is not None:
        address_form_class = get_address_form_class(instance.country.code)
        address_form = address_form_class(
            data, instance=instance, enable_normalization=enable_normalization, **kwargs
        )
    else:
        initial_address = (
            initial if not preview else data.dict() if data is not None else data
        )
        address_form = address_form_class(
            not preview and data or None,
            initial=initial_address,
            enable_normalization=enable_normalization,
            **kwargs,
        )

    if hasattr(address_form.fields["country_area"], "choices"):
        choices = address_form.fields["country_area"].choices
        choices = [(choice[1], choice[1]) for choice in choices]
        address_form.fields["country_area"].choices = choices
    return address_form, preview
