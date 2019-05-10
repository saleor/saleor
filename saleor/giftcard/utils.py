import uuid


def generate_gift_card_code():
    """Generate new unique gift card code."""
    return str(uuid.uuid4()).replace("-", "").upper()[:16]
