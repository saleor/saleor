import i18naddress

original_load_validation_data = i18naddress.load_validation_data


COUNTRIES_RULES_OVERRIDE = {
    "JP": {
        # Library `google-i18n-address` use `AddressValidationMetadata` form Google to provide required fields.
        # During address normalization, unexpected or unnecessary fields are removed. In `Japanse` address, `city` field
        # is not marked as `allowed_field` in `AddressValidationMetadata`. This causes the `city` field to be removed
        # https://github.com/google/libaddressinput/issues/244
        "fmt": "〒%Z%n%S%n%C%n%A%n%O%n%N",
        "lfmt": "%N%n%O%n%A, %C, %S%n%Z",
    },
}


def patched_load_validation_data(country_code="all"):
    validation_data = original_load_validation_data(country_code)
    upper_country_code = country_code.upper()
    if rules_override := COUNTRIES_RULES_OVERRIDE.get(upper_country_code):
        for key, value in rules_override.items():
            validation_data[upper_country_code][key] = value
    return validation_data


def i18n_rules_override():
    i18naddress.load_validation_data = patched_load_validation_data
