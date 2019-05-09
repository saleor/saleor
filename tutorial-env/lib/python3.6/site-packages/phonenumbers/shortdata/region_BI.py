"""Auto-generated file, do not edit by hand. BI metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BI = PhoneMetadata(id='BI', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[16-9]\\d{2,3}', possible_length=(3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='11[237]|611', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='11[237]', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1\\d|5[2-9]|6[0-256])|611|7(?:10|77|979)|8[28]8|900', example_number='110', possible_length=(3, 4)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='611|7(?:10|77)|888|900', example_number='611', possible_length=(3,)),
    sms_services=PhoneNumberDesc(national_number_pattern='(?:71|90)0', example_number='710', possible_length=(3,)),
    short_data=True)
