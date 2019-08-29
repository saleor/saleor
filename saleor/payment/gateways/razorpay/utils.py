from decimal import Decimal


def get_error_response(amount: Decimal, **additional_kwargs) -> dict:
    """Create a placeholder response for invalid or failed requests.

    It is used to generate a failed transaction object.
    """
    return {"is_success": False, "amount": amount, **additional_kwargs}


def get_amount_for_razorpay(amount: Decimal) -> int:
    """Convert an amount of Indian rupees to paisa (needed by Razorpay).

    Multiplies the value by 100.
    """
    return int(amount * 100)
