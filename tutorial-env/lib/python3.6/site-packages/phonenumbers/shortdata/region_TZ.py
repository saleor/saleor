"""Auto-generated file, do not edit by hand. TZ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_TZ = PhoneMetadata(id='TZ', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[149]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='11[12]|999', example_number='111', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='11[12]|999', example_number='111', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='11[12]|46400|999', example_number='111', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='464\\d\\d', example_number='46400', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='464\\d\\d', example_number='46400', possible_length=(5,)),
    short_data=True)
