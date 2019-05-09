"""Auto-generated file, do not edit by hand. BW metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BW = PhoneMetadata(id='BW', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='99[7-9]', example_number='997', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='99[7-9]', example_number='997', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='13123|99[7-9]', example_number='997', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='131\\d\\d', example_number='13100', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='131\\d\\d', example_number='13100', possible_length=(5,)),
    short_data=True)
