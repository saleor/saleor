from allauth.account.adapter import DefaultAccountAdapter
from django.core.urlresolvers import reverse


class AccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return reverse('cart:assign-and-redirect')
