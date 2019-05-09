"""Auto-generated file, do not edit by hand. SI metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_SI = PhoneMetadata(id='SI', country_code=386, international_prefix='00|10(?:22|66|88|99)',
    general_desc=PhoneNumberDesc(national_number_pattern='[1-7]\\d{7}|8\\d{4,7}|90\\d{4,6}', possible_length=(5, 6, 7, 8), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:[1-357][2-8]|4[24-8])\\d{6}', example_number='12345678', possible_length=(8,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='6(?:5(?:1\\d|55|[67]0)|9(?:10|[69]\\d))\\d{4}|(?:[37][01]|4[0139]|51|6[48])\\d{6}', example_number='31234567', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80\\d{4,6}', example_number='80123456', possible_length=(6, 7, 8)),
    premium_rate=PhoneNumberDesc(national_number_pattern='89[1-3]\\d{2,5}|90\\d{4,6}', example_number='90123456', possible_length=(5, 6, 7, 8)),
    voip=PhoneNumberDesc(national_number_pattern='(?:59\\d\\d|8(?:1(?:[67]\\d|8[01389])|2(?:0\\d|2[0378]|8[0-2489])|3[389]\\d))\\d{4}', example_number='59012345', possible_length=(8,)),
    preferred_international_prefix='00',
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{3,6})', format='\\1 \\2', leading_digits_pattern=['8[09]|9'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{5})', format='\\1 \\2', leading_digits_pattern=['59|8'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[37][01]|4[0139]|51|6'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d)(\\d{3})(\\d{2})(\\d{2})', format='\\1 \\2 \\3 \\4', leading_digits_pattern=['[1-57]'], national_prefix_formatting_rule='(0\\1)')],
    mobile_number_portable_region=True)
