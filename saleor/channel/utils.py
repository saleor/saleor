from .models import Channel


def raise_channel_validation():
    """Enable validation if there are more than 2 channels."""
    count = Channel.objects.count()
    if count >= 2:
        return True
    return False
