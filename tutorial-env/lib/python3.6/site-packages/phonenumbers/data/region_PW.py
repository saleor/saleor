"""Auto-generated file, do not edit by hand. PW metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_PW = PhoneMetadata(id='PW', country_code=680, international_prefix='01[12]',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[25-8]\\d\\d|345|488|900)\\d{4}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2(?:55|77)|345|488|5(?:35|44|87)|6(?:22|54|79)|7(?:33|47)|8(?:24|55|76)|900)\\d{4}', example_number='2771234', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:6[2-4689]0|77\\d|88[0-4])\\d{4}', example_number='6201234', possible_length=(7,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1 \\2', leading_digits_pattern=['[2-9]'])])
