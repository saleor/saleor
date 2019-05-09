"""Auto-generated file, do not edit by hand. KI metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_KI = PhoneMetadata(id='KI', country_code=686, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[37]\\d|6[0-79])\\d{6}|(?:[2-48]\\d|50)\\d{3}', possible_length=(5, 8)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:[24]\\d|3[1-9]|50|65(?:02[12]|12[56]|22[89]|[3-5]00)|7(?:27\\d\\d|3100|5(?:02[12]|12[56]|22[89]|[34](?:00|81)|500))|8[0-5])\\d{3}', example_number='31234', possible_length=(5, 8)),
    mobile=PhoneNumberDesc(national_number_pattern='73140\\d{3}|(?:630[01]|730[0-5])\\d{4}|[67]200[01]\\d{3}', example_number='72001234', possible_length=(8,)),
    voip=PhoneNumberDesc(national_number_pattern='30(?:0[01]\\d\\d|12(?:11|20))\\d\\d', example_number='30010000', possible_length=(8,)),
    national_prefix='0',
    national_prefix_for_parsing='0')
