"""Auto-generated file, do not edit by hand. SG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SG = PhoneMetadata(id='SG', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[179]\\d{2,4}', possible_length=(3, 4, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='99[359]', example_number='993', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='99[359]', example_number='993', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:[0136]\\d\\d|[57]\\d{2,3}|[89](?:0[1-9]|[1-9]\\d))|77222|99[02-9]', example_number='990', possible_length=(3, 4, 5)),
    sms_services=PhoneNumberDesc(national_number_pattern='772\\d\\d', example_number='77200', possible_length=(5,)),
    short_data=True)
