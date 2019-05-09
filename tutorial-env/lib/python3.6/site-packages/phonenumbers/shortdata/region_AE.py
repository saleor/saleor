"""Auto-generated file, do not edit by hand. AE metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_AE = PhoneMetadata(id='AE', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[149]\\d{2,3}', possible_length=(3, 4)),
    toll_free=PhoneNumberDesc(national_number_pattern='112|99[7-9]', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='112|99[7-9]', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='112|445[16]|99[7-9]', example_number='112', possible_length=(3, 4)),
    sms_services=PhoneNumberDesc(national_number_pattern='445\\d', example_number='4450', possible_length=(4,)),
    short_data=True)
