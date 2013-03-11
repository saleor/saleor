from django.core.urlresolvers import reverse


def callback_url(service):
    return "http://localhost:8000" + reverse('registration:oauth_callback',
                                             kwargs={'service': service})
