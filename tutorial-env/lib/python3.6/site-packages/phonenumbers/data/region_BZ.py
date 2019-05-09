"""Auto-generated file, do not edit by hand. BZ metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BZ = PhoneMetadata(id='BZ', country_code=501, international_prefix='00',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:0800\\d|[2-8])\\d{6}', possible_length=(7, 11)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:236|732)\\d{4}|[2-578][02]\\d{5}', example_number='2221234', possible_length=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='6[0-35-7]\\d{5}', example_number='6221234', possible_length=(7,)),
    toll_free=PhoneNumberDesc(national_number_pattern='0800\\d{7}', example_number='08001234123', possible_length=(11,)),
    number_format=[NumberFormat(pattern='(\\d{3})(\\d{4})', format='\\1-\\2', leading_digits_pattern=['[2-8]']),
        NumberFormat(pattern='(\\d)(\\d{3})(\\d{4})(\\d{3})', format='\\1-\\2-\\3-\\4', leading_digits_pattern=['0'])])
