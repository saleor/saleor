from django.conf import settings
from django.utils.module_loading import import_string

import six

from templated_email.backends.vanilla_django import TemplateBackend
from templated_email.utils import InlineImage  # noqa


def get_connection(backend=None, template_prefix=None, template_suffix=None,
                   fail_silently=False, **kwargs):
    """Load a templated e-mail backend and return an instance of it.

    If backend is None (default) settings.TEMPLATED_EMAIL_BACKEND is used.

    Both fail_silently and other keyword arguments are used in the
    constructor of the backend.
    """
    # This method is mostly a copy of the backend loader present in
    # django.core.mail.get_connection
    klass_path = backend or getattr(settings, 'TEMPLATED_EMAIL_BACKEND',
                                    TemplateBackend)
    if isinstance(klass_path, six.string_types):
        try:
            # First check if class name is omitted and we have module in settings
            klass = import_string(klass_path + '.' + 'TemplateBackend')
        except ImportError:
            # Fallback to class name
            klass = import_string(klass_path)
    else:
        klass = klass_path

    return klass(fail_silently=fail_silently, template_prefix=template_prefix,
                 template_suffix=template_suffix, **kwargs)


def get_templated_mail(template_name, context, from_email=None, to=None,
                       cc=None, bcc=None, headers=None,
                       template_prefix=None, template_suffix=None,
                       template_dir=None, file_extension=None,
                       create_link=False):
    """Returns a templated EmailMessage instance without a connection using
    the django templating backend."""
    template_prefix = template_prefix or template_dir
    template_suffix = template_suffix or file_extension
    templater = TemplateBackend(template_prefix=template_prefix,
                                template_suffix=template_suffix)
    return templater.get_email_message(template_name, context,
                                       from_email=from_email, to=to,
                                       cc=cc, bcc=bcc, headers=headers,
                                       template_prefix=template_prefix,
                                       template_suffix=template_suffix,
                                       create_link=create_link)


def send_templated_mail(template_name, from_email, recipient_list, context,
                        cc=None, bcc=None, fail_silently=False, connection=None,
                        headers=None, template_prefix=None,
                        template_suffix=None,
                        create_link=False, **kwargs):
    """Easy wrapper for sending a templated email to a recipient list.

    Final behaviour of sending depends on the currently selected engine.
    See BackendClass.send.__doc__
    """
    connection = connection or get_connection(template_prefix=template_prefix,
                                              template_suffix=template_suffix)
    return connection.send(template_name, from_email, recipient_list, context,
                           cc=cc, bcc=bcc, fail_silently=fail_silently,
                           headers=headers, create_link=create_link, **kwargs)
