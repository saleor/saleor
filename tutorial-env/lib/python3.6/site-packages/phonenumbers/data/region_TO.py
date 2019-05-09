"""Auto-generated file, do not edit by hand. TO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TO = PhoneMetadata(id='TO', country_code=676, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[78]\\d{6}|[2-478]\\d{4}|(?:080|[56])0\\d{3}', possible_length=(5, 7)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2\\d|3[1-8]|4[1-4]|[56]0|7[0149]|8[05])\\d{3}', example_number='20123', possible_length=(5,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:7[578]|8[46-9])\\d{5}', example_number='7715123', possible_length=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='0800\\d{3}', example_number='0800222', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})', format='\\1-\\2', leading_digits_pattern=['[2-6]|7[014]|8[05]']),
        NumberFormat(pattern='(\\d{4})(\\d{3})', format='\\1 \\2', leading_digits_pattern=['0']),
        NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['7[578]|8'])])
