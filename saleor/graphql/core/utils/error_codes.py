DJANGO_VALIDATORS_ERROR_CODES = [
    "invalid",
    "limit_value",
    "max_value",
    "min_value",
    "min_length",
    "max_length",
    "max_digits",
    "max_decimal_places",
    "max_whole_digits",
    "invalid_extension",
    "null_characters_not_allowed",
]

DJANGO_FORM_FIELDS_ERROR_CODES = [
    "overflow",
    "missing",
    "empty",
    "contradiction",
    "invalid_image",
    "invalid_choice",
    "invalid_list",
    "incomplete",
    "invalid_date",
    "invalid_time",
]

ERROR_CODE_UNKNOWN = "unknown"

ERROR_CODES = (
    [ERROR_CODE_UNKNOWN]
    + DJANGO_VALIDATORS_ERROR_CODES
    + DJANGO_FORM_FIELDS_ERROR_CODES
)


def get_error_code_from_error(error):
    """ """
    code = error.code
    if code not in ERROR_CODES:
        return ERROR_CODE_UNKNOWN
    return code
