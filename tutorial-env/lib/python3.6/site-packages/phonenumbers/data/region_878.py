"""Auto-generated file, do not edit by hand. 878 metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_878 = PhoneMetadata(id='001', country_code=878, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='10\\d{10}', possible_length=(12,)),
    voip=PhoneNumberDesc(national_number_pattern='10\\d{10}', example_number='101234567890', possible_length=(12,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{5})(\\d{5})', format='\\1 \\2 \\3', leading_digits_pattern=['1'])])
