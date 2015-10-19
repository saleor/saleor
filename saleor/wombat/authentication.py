from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import BaseAuthentication
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class WombatAuthentication(BaseAuthentication):
    def authenticate(self, request):
        store_id = request.META.get('X-Hub-Store')
        access_token = request.META.get('X-Hub-Access-Token')
        wombat_username = getattr(settings, 'WOMBAT_USERNAME', 'wombat')

        if (store_id == settings.WOMBAT_STORE_ID and
                access_token in settings.WOMBAT_ALLOWED_INTEGRATION_TOKENS):
            wombat = User.objects.get_or_create(email=wombat_username)
            if wombat.is_active:
                return (wombat, None)
        return None
