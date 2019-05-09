"""Auto-generated file, do not edit by hand. MC metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MC = PhoneMetadata(id='MC', country_code=377, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='870\\d{5}|(?:[349]|6\\d)\\d{7}', possible_length=(8, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:870|9[2-47-9]\\d)\\d{5}', example_number='99123456', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='4(?:4\\d|5[1-9])\\d{5}|(?:3|6\\d)\\d{7}', example_number='612345678', possible_length=(8, 9)),
    toll_free=PhoneNumberDesc(national_number_pattern='90\\d{6}', example_number='90123456', possible_length=(8,)),
    no_international_dialling=PhoneNumberDesc(national_number_pattern='870\\d{5}', possible_length=(8,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{2})', format='\\1 \\2 \\3', leading_digits_pattern=['8']),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['4'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[39]']),
        NumberFormat(pattern='(\\d)(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4 \\5', leading_digits_pattern=['6'], national_prefix_formatting_rule='0\\1')],
    intl_number_format=[NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['4']),
        NumberFormat(pattern='(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[39]']),
        NumberFormat(pattern='(\\d)(\\d{2})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4 \\5', leading_digits_pattern=['6'])])
