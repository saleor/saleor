"""Auto-generated file, do not edit by hand. MH metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_MH = PhoneMetadata(id='MH', country_code=692, international_prefix='011',
    general_desc=PhoneNumberDesc(national_number_pattern='329\\d{4}|(?:[256]\\d|45)\\d{5}', possible_length=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:247|528|625)\\d{4}', example_number='2471234', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='(?:(?:23|54)5|329|45[56])\\d{4}', example_number='2351234', possible_length=(7,)),
    voip=PhoneNumberDesc(national_number_pattern='635\\d{4}', example_number='6351234', possible_length=(7,)),
    national_prefix='1',
    national_prefix_for_parsing='1',
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1-\\2', leading_digits_pattern=['[2-6]'])])
