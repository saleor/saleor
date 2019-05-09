"""Auto-generated file, do not edit by hand. 800 metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_800 = PhoneMetadata(id='001', country_code=800, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='\\d{8}', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='\\d{8}', example_number='12345678', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2')])
