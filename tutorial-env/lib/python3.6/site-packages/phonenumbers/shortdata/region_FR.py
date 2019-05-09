"""Auto-generated file, do not edit by hand. FR metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_FR = PhoneMetadata(id='FR', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[1-8]\\d{1,5}', possible_length=(2, 3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='1(?:0(?:07|13)|1[02459]|[578]|9[167])|224|(?:3370|74)0|(?:116\\d|3[01])\\d\\d', example_number='15', possible_length=(2, 3, 4, 5, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='(?:118|[4-8]\\d)\\d{3}|36665', example_number='36665', possible_length=(5, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='1(?:12|[578])', example_number='15', possible_length=(2, 3)),
    short_code=PhoneNumberDesc(national_number_pattern='1(?:0\\d\\d|1(?:[02459]|6(?:000|111)|8\\d{3})|[578]|9[167])|2(?:0(?:00|2)0|24)|[3-8]\\d{4}|3\\d{3}|6(?:1[14]|34)|7(?:0[06]|22|40)', example_number='15', possible_length=(2, 3, 4, 5, 6)),
    standard_rate=PhoneNumberDesc(national_number_pattern='10(?:[13]4|2[23]|99)|202\\d|3(?:646|9[07]0)|634|70[06]|(?:106|61)[14]', example_number='611', possible_length=(3, 4)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='118777|224|6(?:1[14]|34)|7(?:0[06]|22|40)|20(?:0\\d|2)\\d', example_number='224', possible_length=(3, 4, 5, 6)),
    sms_services=PhoneNumberDesc(national_number_pattern='114|[3-8]\\d{4}', example_number='114', possible_length=(3, 5)),
    short_data=True)
