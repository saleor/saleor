"""Auto-generated file, do not edit by hand. WS metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_WS = PhoneMetadata(id='WS', country_code=685, international_prefix='0',
    general_desc=PhoneNumberDesc(national_number_pattern='[2-6]\\d{4}|8\\d{5}(?:\\d{4})?|[78]\\d{6}', possible_length=(5, 6, 7, 10)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:[2-5]\\d|6[1-9])\\d{3}', example_number='22123', possible_length=(5,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:7[25-7]|8(?:[3-7]|9\\d{3}))\\d{5}', example_number='7212345', possible_length=(7, 10)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{3}', example_number='800123', possible_length=(6,)),
    number_format=[NumberFormat(pattern='(\\d{5})', format='\\1', leading_digits_pattern=['[2-6]']),
        NumberFormat(pattern='(\\d{3})(\\d{3,7})', format='\\1 \\2', leading_digits_pattern=['8']),
        NumberFormat(pattern='(\\d{2})(\\d{5})', format='\\1 \\2', leading_digits_pattern=['7'])])
