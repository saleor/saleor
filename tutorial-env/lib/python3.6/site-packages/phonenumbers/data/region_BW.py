"""Auto-generated file, do not edit by hand. BW metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BW = PhoneMetadata(id='BW', country_code=267, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='90\\d{5}|(?:[2-6]|7\\d)\\d{6}', possible_length=(7, 8)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2(?:4[0-48]|6[0-24]|9[0578])|3(?:1[0-35-9]|55|[69]\\d|7[013])|4(?:6[03]|7[1267]|9[0-5])|5(?:3[0389]|4[0489]|7[1-47]|88|9[0-49])|6(?:2[1-35]|5[149]|8[067]))\\d{4}', example_number='2401234', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='77200\\d{3}|7(?:[1-6]\\d|7[014-8])\\d{5}', example_number='71123456', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90\\d{5}', example_number='9012345', possible_length=(7,)),
    voip=PhoneNumberDesc(national_number_pattern='79(?:1(?:[01]\\d|20)|2[0-2]\\d)\\d{3}', example_number='79101234', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{5})', format='\\1 \\2', leading_digits_pattern=['90']),
        NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[2-6]']),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['7'])])
