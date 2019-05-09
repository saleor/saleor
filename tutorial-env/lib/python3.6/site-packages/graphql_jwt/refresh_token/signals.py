from django.dispatch import Signal

refresh_token_revoked = Signal(providing_args=['refresh_token'])
refresh_token_rotated = Signal(providing_args=['refresh_token'])
