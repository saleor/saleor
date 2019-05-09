"""Auto-generated file, do not edit by hand. KG metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_KG = PhoneMetadata(id='KG', country_code=996, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[235-7]\\d|99)\\d{7}|800\\d{6,7}', possible_length=(9, 10), possible_length_local_only=(5, 6)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:3(?:1(?:[256]\\d|3[1-9]|47)|2(?:22|3[0-479]|6[0-7])|4(?:22|5[6-9]|6\\d)|5(?:22|3[4-7]|59|6\\d)|6(?:22|5[35-7]|6\\d)|7(?:22|3[468]|4[1-9]|59|[67]\\d)|9(?:22|4[1-8]|6\\d))|6(?:09|12|2[2-4])\\d)\\d{5}', example_number='312123456', possible_length=(9,), possible_length_local_only=(5, 6)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:2(?:0[0-35]|2\\d)|5(?:0[0-57-9]|[124-7]\\d)|7(?:[07]\\d|55)|99[69])\\d{6}', example_number='700123456', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{6,7}', example_number='800123456', possible_length=(9, 10)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{4})(\\d{5})', format='\\1 \\2', leading_digits_pattern=['3(?:1[346]|[24-79])'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[235-79]'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d)(\\d{2,3})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['8'], national_prefix_formatting_rule='0\\1')])
