"""Auto-generated file, do not edit by hand. ES metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_ES = PhoneMetadata(id='ES', country_code=None, international_prefix=None,
    general_desc=PhoneNumberDesc(national_number_pattern='[0-379]\\d{2,5}', possible_length=(3, 4, 5, 6)),
    toll_free=PhoneNumberDesc(national_number_pattern='0(?:16|6[57]|8[58])|1(?:006|12|[3-7]\\d\\d)|(?:116|20\\d)\\d{3}', example_number='016', possible_length=(3, 4, 6)),
    premium_rate=PhoneNumberDesc(national_number_pattern='[12]2\\d{1,4}|90(?:5\\d|7)|(?:118|2(?:[357]\\d|80)|3[357]\\d)\\d\\d|[79]9[57]\\d{3}', example_number='120', possible_length=(3, 4, 5, 6)),
    emergency=PhoneNumberDesc(national_number_pattern='08[58]|112', example_number='085', possible_length=(3,)),
    short_code=PhoneNumberDesc(national_number_pattern='0(?:1[0-26]|6[0-257]|8[058]|9[12])|1(?:0[03-57]\\d{1,3}|1(?:2|6(?:000|111)|8\\d\\d)|2\\d{1,4}|[3-9]\\d\\d)|2(?:2\\d{1,4}|80\\d\\d)|90(?:5[124578]|7)|1(?:3[34]|77)|(?:2[01]\\d|[79]9[57])\\d{3}|[23][357]\\d{3}', example_number='010', possible_length=(3, 4, 5, 6)),
    standard_rate=PhoneNumberDesc(national_number_pattern='0(?:[16][0-2]|80|9[12])|21\\d{4}', example_number='010', possible_length=(3, 6)),
    carrier_specific=PhoneNumberDesc(national_number_pattern='1(?:3[34]|77)|[12]2\\d{1,4}', example_number='120', possible_length=(3, 4, 5, 6)),
    sms_services=PhoneNumberDesc(national_number_pattern='(?:2[0-2]\\d|3[357]|[79]9[57])\\d{3}|2(?:[2357]\\d|80)\\d\\d', example_number='22000', possible_length=(5, 6)),
    short_data=True)
