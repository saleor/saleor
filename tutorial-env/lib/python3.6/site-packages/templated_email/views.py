from django.views.generic import DetailView

from templated_email.models import SavedEmail


class ShowEmailView(DetailView):
    model = SavedEmail
    template_name = 'templated_email/saved_email.html'
    slug_field = 'uuid'
    slug_url_kwarg = 'uuid'
