"""Auto-generated file, do not edit by hand. CA metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CA = PhoneMetadata(id='CA', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[1-9]\\d\\d(?:\\d\\d(?:\\d(?:\\d{2})?)?)?', possible_length=(3, 5, 6, 8)),
    toll_free=PhoneNumberDesc(national_number_pattern='112|[29]11', example_number='112', possible_length=(3,)),
    emergency=PhoneNumberDesc(national_number_pattern='112|911', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='112|30000\\d{3}|[1-35-9]\\d{4,5}|[2-9]11', example_number='112', possible_length=(3, 5, 6, 8)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='[235-7]11', example_number='211', possible_length=(3,)),
    sms_services=PhoneNumberDesc(national_number_pattern='300\\d{5}|[1-35-9]\\d{4,5}', example_number='10000', possible_length=(5, 6, 8)),
    short_data=True)
