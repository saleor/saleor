"""Auto-generated file, do not edit by hand. NG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_NG = PhoneMetadata(id='NG', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[14]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='199', example_number='199', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='199', example_number='199', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='199|40700', example_number='199', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='407\\d\\d', example_number='40700', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='407\\d\\d', example_number='40700', possible_length=(5,)),
    short_data=True)
