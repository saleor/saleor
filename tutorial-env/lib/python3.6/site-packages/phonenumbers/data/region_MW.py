"""Auto-generated file, do not edit by hand. MW metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MW = PhoneMetadata(id='MW', country_code=265, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='1\\d{6}(?:\\d{2})?|(?:[23]1|77|88|99)\\d{7}', possible_length=(7, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:1[2-9]|21\\d\\d)\\d{5}', example_number='1234567', possible_length=(7, 9)),
    mobile=PhoneNumberDesc(national_number_pattern='111\\d{6}|(?:77|88|99)\\d{7}', example_number='991234567', possible_length=(9,)),
    voip=PhoneNumberDesc(national_number_pattern='31\\d{7}', example_number='310123456', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d)(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['1[2-9]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['2'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['3'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[17-9]'], national_prefix_formatting_rule='0\\1')])
