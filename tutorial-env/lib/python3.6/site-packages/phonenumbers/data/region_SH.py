"""Auto-generated file, do not edit by hand. SH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SH = PhoneMetadata(id='SH', country_code=290, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[256]\\d|8)\\d{3}', possible_length=(4, 5)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2(?:[0-57-9]\\d|6[4-9])\\d\\d', example_number='22158', possible_length=(4, 5)),
    mobile=PhoneNumberDesc(national_number_pattern='[56]\\d{4}', example_number='51234', possible_length=(5,)),
    voip=PhoneNumberDesc(national_number_pattern='262\\d\\d', example_number='26212', possible_length=(5,)),
    main_country_for_code=True,
    leading_digits='[256]')
