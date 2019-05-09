"""Auto-generated file, do not edit by hand. IS metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_IS = PhoneMetadata(id='IS', country_code=354, international_prefix='00|1(?:0(?:01|[12]0)|100)',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:38\\d|[4-9])\\d{6}', possible_length=(7, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:4(?:1[0-24-69]|2[0-7]|[37][0-8]|4[0-245]|5[0-68]|6\\d|8[0-36-8])|5(?:05|[156]\\d|2[02578]|3[0-579]|4[03-7]|7[0-2578]|8[0-35-9]|9[013-689])|87[23])\\d{4}', example_number='4101234', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:38[589]\\d\\d|6(?:1[1-8]|2[0-6]|3[027-9]|4[014679]|5[0159]|6[0-69]|70|8[06-8]|9\\d)|7(?:5[057]|[6-8]\\d|9[0-3])|8(?:2[0-59]|[3469]\\d|5[1-9]|8[28]))\\d{4}', example_number='6111234', possible_length=(7, 9)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{4}', example_number='8001234', possible_length=(7,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90\\d{5}', example_number='9011234', possible_length=(7,)),
    voip=PhoneNumberDesc(national_number_pattern='49\\d{5}', example_number='4921234', possible_length=(7,)),
    uan=PhoneNumberDesc(national_number_pattern='809\\d{4}', example_number='8091234', possible_length=(7,)),
    voicemail=PhoneNumberDesc(national_number_pattern='(?:689|8(?:7[0189]|80)|95[48])\\d{4}', example_number='6891234', possible_length=(7,)),
    preferred_international_prefix='00',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[4-9]']),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['3'])],
    mobile_number_portable_region=True)
