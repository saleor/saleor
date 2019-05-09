"""Auto-generated file, do not edit by hand. EH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_EH = PhoneMetadata(id='EH', country_code=212, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[5-8]\\d{8}', possible_length=(9,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='528[89]\\d{5}', example_number='528812345', possible_length=(9,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:6(?:[0-79]\\d|8[0-247-9])|7(?:0[06-8]|6[1267]|7[017]))\\d{6}', example_number='650123456', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80\\d{7}', example_number='801234567', possible_length=(9,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='89\\d{7}', example_number='891234567', possible_length=(9,)),
    voip=PhoneNumberDesc(national_number_pattern='5924[01]\\d{4}', example_number='592401234', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    leading_digits='528[89]')
