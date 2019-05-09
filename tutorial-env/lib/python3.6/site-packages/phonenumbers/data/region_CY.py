"""Auto-generated file, do not edit by hand. CY metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_CY = PhoneMetadata(id='CY', country_code=357, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[279]\\d|[58]0)\\d{6}', possible_length=(8,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='2[2-6]\\d{6}', example_number='22345678', possible_length=(8,)),
    mobile=PhoneNumberDesc(national_number_pattern='9[4-79]\\d{6}', example_number='96123456', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='800\\d{5}', example_number='80001234', possible_length=(8,)),
    premium_rate=PhoneNumberDesc(national_number_pattern='90[09]\\d{5}', example_number='90012345', possible_length=(8,)),
    shared_cost=PhoneNumberDesc(national_number_pattern='80[1-9]\\d{5}', example_number='80112345', possible_length=(8,)),
    personal_number=PhoneNumberDesc(national_number_pattern='700\\d{5}', example_number='70012345', possible_length=(8,)),
    uan=PhoneNumberDesc(national_number_pattern='(?:50|77)\\d{6}', example_number='77123456', possible_length=(8,)),
    number_format=[NumberFormat(pattern='(\\d{2})(\\d{6})', format='\\1 \\2', leading_digits_pattern=['[257-9]'])],
    mobile_number_portable_region=True)
