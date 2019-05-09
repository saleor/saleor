"""Auto-generated file, do not edit by hand. BH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BH = PhoneMetadata(id='BH', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[0189]\\d\\d(?:\\d{2})?', possible_length=(3, 5)),
    toll_free=PhoneNumberDesc(national_number_pattern='(?:0[167]|81)\\d{3}|[19]99', example_number='199', possible_length=(3, 5)),
    premium_rate=PhoneNumberDesc(national_number_pattern='9[148]\\d{3}', example_number='91000', possible_length=(5,)),
    emergency=PhoneNumberDesc(national_number_pattern='[19]99', example_number='199', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:[02]\\d|12|4[01]|51|8[18]|9[169])|99[02489]|(?:0[167]|8[158]|9[148])\\d{3}', example_number='100', possible_length=(3, 5)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='0[67]\\d{3}|88000|98555', example_number='06000', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='88000|98555', example_number='88000', possible_length=(5,)),
    short_data=True)
