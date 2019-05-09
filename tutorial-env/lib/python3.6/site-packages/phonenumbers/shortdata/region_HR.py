"""Auto-generated file, do not edit by hand. HR metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_HR = PhoneMetadata(id='HR', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[19]\\d{1,5}', possible_length=(2, 3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:12|9[2-4])|9[34]|1(?:16\\d|39)\\d\\d', example_number='93', possible_length=(2, 3, 5, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='118\\d\\d', example_number='11800', possible_length=(5,)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:12|9[2-4])|9[34]', example_number='93', possible_length=(2, 3)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:1(?:2|6(?:00[06]|1(?:1[17]|23))|8\\d\\d)|3977|9(?:[2-5]|87))|9[34]', example_number='93', possible_length=(2, 3, 4, 5, 6)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='139\\d\\d', example_number='13900', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='139\\d\\d', example_number='13900', possible_length=(5,)),
    short_data=True)
