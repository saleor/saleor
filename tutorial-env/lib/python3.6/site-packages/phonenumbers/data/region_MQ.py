"""Auto-generated file, do not edit by hand. MQ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MQ = PhoneMetadata(id='MQ', country_code=596, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:596|69\\d)\\d{6}', possible_length=(9,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='596(?:0[0-7]|10|2[7-9]|3[05-9]|4[0-46-8]|[5-7]\\d|8[09]|9[4-8])\\d{4}', example_number='596301234', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='69(?:6(?:[0-47-9]\\d|5[0-6]|6[0-4])|727)\\d{4}', example_number='696201234', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[56]'], national_prefix_formatting_rule='0\\1')],
    mobile_number_portable_region=True)
