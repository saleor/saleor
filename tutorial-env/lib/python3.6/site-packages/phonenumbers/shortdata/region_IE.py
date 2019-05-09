"""Auto-generated file, do not edit by hand. IE metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_IE = PhoneMetadata(id='IE', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[159]\\d{2,5}', possible_length=(3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='11(?:2|6\\d{3})|999', example_number='112', possible_length=(3, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='5[37]\\d{3}', example_number='53000', possible_length=(5,)),
    emergency=PhoneNumberDesc(national_number_pattern='112|999', example_number='112', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='11(?:2|6(?:00[06]|1(?:1[17]|23)))|999|(?:1(?:18|9)|5[0137]\\d)\\d\\d', example_number='112', possible_length=(3, 4, 5, 6)),
    standard_rate=PhoneNumberDesc(national_number_pattern='51\\d{3}', example_number='51000', possible_length=(5,)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='51210', example_number='51210', possible_length=(5,)),
    sms_services=PhoneNumberDesc(national_number_pattern='51210|(?:118|5[037]\\d)\\d\\d', example_number='11800', possible_length=(5,)),
    short_data=True)
