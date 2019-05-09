"""Auto-generated file, do not edit by hand. BO metadata"""
from ..phonemetadata import NumberFormat, PhoneNumberDesc, PhoneMetadata

PHONE_METADATA_BO = PhoneMetadata(id='BO', country_code=591, international_prefix='00(?:1\\d)?',
    general_desc=PhoneNumberDesc(national_number_pattern='(?:[2-467]\\d{3}|80017)\\d{4}', possible_length=(8, 9), possible_length_local_only=(7,)),
    fixed_line=PhoneNumberDesc(national_number_pattern='(?:2(?:2\\d\\d|5(?:11|[258]\\d|9[67])|6(?:12|2\\d|9[34])|8(?:2[34]|39|62))|3(?:3\\d\\d|4(?:6\\d|8[24])|8(?:25|42|5[257]|86|9[25])|9(?:[27]\\d|3[2-4]|4[248]|5[24]|6[2-6]))|4(?:4\\d\\d|6(?:11|[24689]\\d|72)))\\d{4}', example_number='22123456', possible_length=(8,), possible_length_local_only=(7,)),
    mobile=PhoneNumberDesc(national_number_pattern='[67]\\d{7}', example_number='71234567', possible_length=(8,)),
    toll_free=PhoneNumberDesc(national_number_pattern='80017\\d{4}', example_number='800171234', possible_length=(9,)),
    national_prefix='0',
    national_prefix_for_parsing='0(1\\d)?',
    number_format=[NumberFormat(pattern='(\\d)(\\d{7})', format='\\1 \\2', leading_digits_pattern=['[23]|4[46]'], domestic_carrier_code_formatting_rule='0$CC \\1'),
        NumberFormat(pattern='(\\d{8})', format='\\1', leading_digits_pattern=['[67]'], domestic_carrier_code_formatting_rule='0$CC \\1'),
        NumberFormat(pattern='(\\d{3})(\\d{2})(\\d{4})', format='\\1 \\2 \\3', leading_digits_pattern=['8'], domestic_carrier_code_formatting_rule='0$CC \\1')])
