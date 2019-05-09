"""Auto-generated file, do not edit by hand. MW metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MW = PhoneMetadata(id='MW', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[189]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='199|99[7-9]', example_number='199', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='199|99[7-9]', example_number='199', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='199|80400|99[7-9]', example_number='199', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='804\\d\\d', example_number='80400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='804\\d\\d', example_number='80400', possible_length=(5,)),
    short_data=True)
