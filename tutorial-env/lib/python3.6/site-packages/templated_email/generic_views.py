from functools import partial

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from templated_email import send_templated_mail


class TemplatedEmailFormViewMixin(object):
    templated_email_template_name = None
    templated_email_send_on_success = True
    templated_email_send_on_failure = False
    templated_email_from_email = partial(getattr, settings, 'TEMPLATED_EMAIL_FROM_EMAIL', None)

    def templated_email_get_template_names(self, valid):
        if self.templated_email_template_name is None:
            raise ImproperlyConfigured(
                "TemplatedEmailFormViewMixin requires either a definition of "
                "'templated_email_template_name' or an implementation of 'templated_email_get_template_names()'")
        return [self.templated_email_template_name]

    def templated_email_get_context_data(self, **kwargs):
        return kwargs

    def templated_email_get_recipients(self, form):
        raise NotImplementedError('You must implement templated_email_get_recipients method')

    def templated_email_get_send_email_kwargs(self, valid, form):
        if valid:
            context = self.templated_email_get_context_data(form_data=form.data)
        else:
            context = self.templated_email_get_context_data(form_errors=form.errors)
        try:
            from_email = self.templated_email_from_email()
        except TypeError:
            from_email = self.templated_email_from_email
        return {
            'template_name': self.templated_email_get_template_names(valid=valid),
            'from_email': from_email,
            'recipient_list': self.templated_email_get_recipients(form),
            'context': context
        }

    def templated_email_send_templated_mail(self, *args, **kwargs):
        return send_templated_mail(*args, **kwargs)

    def form_valid(self, form):
        response = super(TemplatedEmailFormViewMixin, self).form_valid(form)
        if self.templated_email_send_on_success:
            self.templated_email_send_templated_mail(
                **self.templated_email_get_send_email_kwargs(valid=True, form=form))
        return response

    def form_invalid(self, form):
        response = super(TemplatedEmailFormViewMixin, self).form_invalid(form)
        if self.templated_email_send_on_failure:
            self.templated_email_send_templated_mail(
                **self.templated_email_get_send_email_kwargs(valid=False, form=form))
        return response
