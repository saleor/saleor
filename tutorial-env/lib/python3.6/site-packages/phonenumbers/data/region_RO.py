"""Auto-generated file, do not edit by hand. RO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_RO = PhoneMetadata(id='RO', country_code=40, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[237]\\d|[89]0)\\d{7}|[23]\\d{5}', possible_length=(6, 9)),
    fixed_line=PhoneNumberDesc(national_number_pattern='[23][13-6]\\d{7}|(?:2(?:19\\d|[3-6]\\d9)|31\\d\\d)\\d\\d', example_number='211234567', possible_length=(6, 9)),
    mobile=PhoneNumberDesc(national_number_pattern='7120\\d{5}|7(?:[02-7]\\d|1[01]|8[03-8]|99)\\d{6}', example_number='712034567', possible_length=(9,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{6}', example_number='800123456', possible_length=(9,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90[036]\\d{6}', example_number='900123456', possible_length=(9,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='801\\d{6}', example_number='801123456', possible_length=(9,)),
    uan=PhoneNumberDesc(national_number_pattern='37\\d{7}', example_number='372123456', possible_length=(9,)),
    national_prefix='0',
    preferred_extn_prefix=' int ',
    national_prefix_for_parsing='0',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{3})', format='\\1 \\2', leading_digits_pattern=['2[3-6]', '2[3-6]\\d9'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['219|31'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{2})(\\d{3})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['[23]1'], national_prefix_formatting_rule='0\\1'),
        NumberFormat(pattern='(\\d{3})(\\d{3})(\\d{3})', format='\\1 \\2 \\3', leading_digits_pattern=['[237-9]'], national_prefix_formatting_rule='0\\1')],
    mobile_number_portable_region=True)
