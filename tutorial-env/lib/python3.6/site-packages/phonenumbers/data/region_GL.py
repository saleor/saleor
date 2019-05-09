"""Auto-generated file, do not edit by hand. GL metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_GL = PhoneMetadata(id='GL', country_code=299, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:19|[2-689]\\d)\\d{4}', possible_length=(6,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:19|3[1-7]|6[14689]|8[14-79]|9\\d)\\d{4}', example_number='321000', possible_length=(6,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:[25][1-9]|4[2-9])\\d{4}', example_number='221234', possible_length=(6,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80\\d{4}', example_number='801234', possible_length=(6,)),
    voip=PhoneNumberDesc(national_number_pattern='3[89]\\d{4}', example_number='381234', possible_length=(6,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3', leading_digits_pattern=['19|[2-689]'])])
