"""Auto-generated file, do not edit by hand. CF metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CF = PhoneMetadata(id='CF', country_code=236, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[27]\\d{3}|8776)\\d{4}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2[12]\\d{6}', example_number='21612345', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='7[0257]\\d{6}', example_number='70012345', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='8776\\d{4}', example_number='87761234', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[278]'])])
