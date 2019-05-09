"""Auto-generated file, do not edit by hand. LI metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_LI = PhoneMetadata(id='LI', country_code=423, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='90\\d{5}|(?:[2378]|6\\d\\d)\\d{6}', possible_length=(7, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2(?:01|1[27]|22|3\\d|6[02-578]|96)|3(?:33|40|7[0135-7]|8[048]|9[0269]))\\d{4}', example_number='2345678', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='756\\d{4}|(?:6(?:499|5[0-3]\\d|6(?:0[0-7]|10|2[06-9]|39))|7[37-9])\\d{5}', example_number='660234567', possible_length=(7, 9)),
    toll_free=PhoneNumberDesc(national_number_pattern='80(?:02[28]|9\\d\\d)\\d\\d', example_number='8002222', possible_length=(7,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90(?:02[258]|1(?:23|3[14])|66[136])\\d\\d', example_number='9002222', possible_length=(7,)),
    uan=PhoneNumberDesc(national_number_pattern='870(?:28|87)\\d\\d', example_number='8702812', possible_length=(7,)),
    voicemail=PhoneNumberDesc(national_number_pattern='697(?:56|[78]\\d)\\d{4}', example_number='697861234', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0|(10(?:01|20|66))',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3', leading_digits_pattern=['[237-9]'], domestic_carrier_code_formatting_rule='$CC \\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['69'], domestic_carrier_code_formatting_rule='$CC \\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['6'], domestic_carrier_code_formatting_rule='$CC \\1')])
