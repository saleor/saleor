"""Auto-generated file, do not edit by hand. IS metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_IS = PhoneMetadata(id='IS', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d\\d(?:\\d(?:\\d{2})?)?', possible_length=(3, 4, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:12|71\\d)', example_number='112', possible_length=(3, 4)),
    emergency=PhoneNumberDesc(national_number_pattern='112', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1(?:[28]|61(?:16|23))|4(?:00|1[145]|4[0146])|55|7(?:00|17|7[07-9])|8(?:[02]0|1[16-9]|88)|900)', example_number='112', possible_length=(3, 4, 6)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='14(?:0\\d|41)', example_number='1400', possible_length=(4,)),
    sms_services=PhoneNumberDesc(national_number_pattern='1(?:415|90\\d)', example_number='1415', possible_length=(4,)),
    short_data=True)
