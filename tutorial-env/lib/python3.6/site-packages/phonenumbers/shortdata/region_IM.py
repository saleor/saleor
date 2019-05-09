"""Auto-generated file, do not edit by hand. IM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_IM = PhoneMetadata(id='IM', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[189]\\d\\d(?:\\d{2,3})?', possible_length=(3, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='999', example_number='999', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='999', example_number='999', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1\\d\\d(?:\\d{3})?|8(?:6444|9887)|999', example_number='100', possible_length=(3, 5, 6)),
    sms_services=PhoneNumberDesc(national_number_pattern='8(?:64|98)\\d\\d', example_number='86400', possible_length=(5,)),
    short_data=True)
