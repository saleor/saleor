"""Auto-generated file, do not edit by hand. BH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BH = PhoneMetadata(id='BH', country_code=973, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='[136-9]\\d{7}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:1(?:3[1356]|6[0156]|7\\d)\\d|6(?:1[16]\\d|500|6(?:0\\d|3[12]|44|7[7-9]|88)|9[69][69])|7(?:1(?:11|78)|7\\d\\d))\\d{4}', example_number='17001234', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:3(?:[1-4679]\\d|5[013-69]|8[0-47-9])\\d|6(?:3(?:00|33|6[16])|6(?:3[03-9]|[69]\\d|7[0-6])))\\d{4}', example_number='36001234', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80\\d{6}', example_number='80123456', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='(?:87|9[014578])\\d{6}', example_number='90123456', possible_length=(8,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='84\\d{6}', example_number='84123456', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{4})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[13679]|8[047]'])],
    mobile_number_portable_region=True)
