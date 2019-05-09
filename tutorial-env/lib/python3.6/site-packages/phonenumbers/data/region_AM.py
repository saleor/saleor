"""Auto-generated file, do not edit by hand. AM metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_AM = PhoneMetadata(id='AM', country_code=374, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[1-489]\\d|55|60|77)\\d{6}', possible_length=(8,), possible_length_local_only=(5, 6)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:(?:1[0-2]|47)\\d|2(?:2[2-46]|3[1-8]|4[2-69]|5[2-7]|6[1-9]|8[1-7])|3[12]2)\\d{5}', example_number='10123456', possible_length=(8,), possible_length_local_only=(5, 6)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:4[1349]|55|77|88|9[13-9])\\d{6}', example_number='77123456', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{5}', example_number='80012345', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90[016]\\d{5}', example_number='90012345', possible_length=(8,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='80[1-4]\\d{5}', example_number='80112345', possible_length=(8,)),
    voip=PhoneNumberDesc(national_number_pattern='60(?:2[78]|3[5-9]|4[02-9]|5[0-46-9]|[6-8]\\d|90)\\d{4}', example_number='60271234', possible_length=(8,)),
    national_prefix='0',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[89]0'], national_prefix_formatting_rule='0 \\1'),
        NumberFormat(pattern='(\\d{2})(\\d{6})', format='\\1 \\2', leading_digits_pattern=['1|47'], national_prefix_formatting_rule='(0\\1)'),
        NumberFormat(pattern='(\\d{3})(\\d{5})', format='\\1 \\2', leading_digits_pattern=['[23]'], national_prefix_formatting_rule='(0\\1)'),
        NumberFormat(pattern='(\\d{2})(\\d{6})', format='\\1 \\2', leading_digits_pattern=['[4-9]'], national_prefix_formatting_rule='0\\1')],
    mobile_number_portable_region=True)
