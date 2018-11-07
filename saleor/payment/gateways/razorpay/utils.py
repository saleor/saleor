from decimal import Decimal


def get_error_response(amount: Decimal, **additional_kwargs) -> dict:
    """Create a place holder response for invalid/ failed requests
    for generated a failed transaction object."""
    return dict(is_success=False, amount=amount, **additional_kwargs)


def get_amount_for_razorpay(amount: Decimal) -> int:
    """Convert a decimal amount to int, by multiplying the value by 100."""
    return int(amount * 100)
