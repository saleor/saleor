from django.core.exceptions import ValidationError
from phonenumber_field.phonenumber import to_python
from phonenumbers.phonenumberutil import is_possible_number

from .error_codes import AccountErrorCode


def validate_possible_number(phone, country=None):
    """验证给定的电话号码是否可能有效。

    Args:
        phone (str): 要验证的电话号码。
        country (str, optional): 电话号码的国家/地区代码。默认为 None。

    Returns:
        PhoneNumber: 如果电话号码有效，则返回一个 PhoneNumber 对象。

    Raises:
        ValidationError: 如果电话号码无效。
    """
    phone_number = to_python(phone, country)
    if (
        phone_number
        and not is_possible_number(phone_number)
        or not phone_number.is_valid()
    ):
        raise ValidationError(
            "The phone number entered is not valid.",
            code=AccountErrorCode.INVALID.value,
        )
    return phone_number
