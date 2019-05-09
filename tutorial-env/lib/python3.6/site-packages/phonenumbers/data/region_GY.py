"""Auto-generated file, do not edit by hand. GY metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GY = PhoneMetadata(id='GY', country_code=592, international_prefix='001',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:862\\d|9008)\\d{3}|(?:[2-46]\\d|77)\\d{5}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2(?:1[6-9]|2[0-35-9]|3[1-4]|5[3-9]|6\\d|7[0-24-79])|3(?:2[25-9]|3\\d)|4(?:4[0-24]|5[56])|77[1-57])\\d{4}', example_number='2201234', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='6\\d{6}', example_number='6091234', possible_length=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='(?:289|862)\\d{4}', example_number='2891234', possible_length=(7,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='9008\\d{3}', example_number='9008123', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[2-46-9]'])])
