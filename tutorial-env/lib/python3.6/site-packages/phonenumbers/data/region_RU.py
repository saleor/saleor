"""Auto-generated file, do not edit by hand. RU metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_RU = PhoneMetadata(id='RU', country_code=7, international_prefix='810',
    general_desc=PhoneNumberDesc(national_number_pattern='[347-9]\\d{9}', possible_length=(10,), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:3(?:0[12]|4[1-35-79]|5[1-3]|65|8[1-58]|9[0145])|4(?:01|1[1356]|2[13467]|7[1-5]|8[1-7]|9[1-689])|8(?:1[1-8]|2[01]|3[13-6]|4[0-8]|5[15]|6[1-35-79]|7[1-37-9]))\\d{7}', example_number='3011234567', possible_length=(10,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='9\\d{9}', example_number='9123456789', possible_length=(10,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80[04]\\d{7}', example_number='8001234567', possible_length=(10,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='80[39]\\d{7}', example_number='8091234567', possible_length=(10,)),
    personal_number=PhoneNumberDesc(national_number_pattern='808\\d{7}', example_number='8081234567', possible_length=(10,)),
    preferred_international_prefix='8~10',
    national_prefix='8',
    national_prefix_for_parsing='8',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{2})', format='\\1-\\2-\\3', leading_digits_pattern=['[0-79]']),
        NumberFormat(pattern='(\\d{4})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['7(?:1[0-8]|2[1-9])', '7(?:1(?:[0-6]2|7|8[27])|2(?:1[23]|[2-9]2))', '7(?:1(?:[0-6]2|7|8[27])|2(?:13[03-69]|62[013-9]))|72[1-57-9]2'], national_prefix_formatting_rule='8 (\\1)', national_prefix_optional_when_formatting=True),
        NumberFormat(pattern='(\\d{5})(\\d)(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['7(?:1[0-68]|2[1-9])', '7(?:1(?:[06][3-6]|[18]|2[35]|[3-5][3-5])|2(?:[13][3-5]|[24-689]|7[457]))', '7(?:1(?:0(?:[356]|4[023])|[18]|2(?:3[013-9]|5)|3[45]|43[013-79]|5(?:3[1-8]|4[1-7]|5)|6(?:3[0-35-9]|[4-6]))|2(?:1(?:3[178]|[45])|[24-689]|3[35]|7[457]))|7(?:14|23)4[0-8]|71(?:33|45)[1-79]'], national_prefix_formatting_rule='8 (\\1)', national_prefix_optional_when_formatting=True),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['7'], national_prefix_formatting_rule='8 (\\1)', national_prefix_optional_when_formatting=True),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2-\\3-\\4', leading_digits_pattern=['[3489]'], national_prefix_formatting_rule='8 (\\1)', national_prefix_optional_when_formatting=True)],
    intl_number_format=[NumberFormat(pattern='(\\d{4})(\\d{2})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['7(?:1[0-8]|2[1-9])', '7(?:1(?:[0-6]2|7|8[27])|2(?:1[23]|[2-9]2))', '7(?:1(?:[0-6]2|7|8[27])|2(?:13[03-69]|62[013-9]))|72[1-57-9]2']),
        NumberFormat(pattern='(\\d{5})(\\d)(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['7(?:1[0-68]|2[1-9])', '7(?:1(?:[06][3-6]|[18]|2[35]|[3-5][3-5])|2(?:[13][3-5]|[24-689]|7[457]))', '7(?:1(?:0(?:[356]|4[023])|[18]|2(?:3[013-9]|5)|3[45]|43[013-79]|5(?:3[1-8]|4[1-7]|5)|6(?:3[0-35-9]|[4-6]))|2(?:1(?:3[178]|[45])|[24-689]|3[35]|7[457]))|7(?:14|23)4[0-8]|71(?:33|45)[1-79]']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['7']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2-\\3-\\4', leading_digits_pattern=['[3489]'])],
    main_country_for_code=True,
    leading_digits='3[04-689]|[489]')
