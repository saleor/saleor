"""Auto-generated file, do not edit by hand. KM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_KM = PhoneMetadata(id='KM', country_code=269, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[3478]\\d{6}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='7[4-7]\\d{5}', example_number='7712345', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='[34]\\d{6}', example_number='3212345', possible_length=(7,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='8\\d{6}', example_number='8001234', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3', leading_digits_pattern=['[3478]'])])
