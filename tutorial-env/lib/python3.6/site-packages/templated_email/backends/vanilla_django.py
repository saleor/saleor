import uuid
import hashlib
from io import BytesIO

from django.conf import settings
from django.core.mail import get_connection
from django.template import Context
from django.utils.translation import ugettext as _
from django.core.files.storage import default_storage

from templated_email.utils import (
    get_emailmessage_klass, get_emailmultialternatives_klass)
from templated_email.utils import InlineImage
from render_block import render_block_to_string, BlockNotFound


try:
    import html2text
except ImportError:
    html2text = None


class EmailRenderException(Exception):
    pass


class TemplateBackend(object):
    """
    Backend which uses Django's
    templates, and django's send_mail function.

    Heavily inspired by http://stackoverflow.com/questions/2809547/creating-email-templates-with-django

    Default / preferred behaviour works like so:
        templates named
            templated_email/<template_name>.email

        {% block subject %} declares the subject
        {% block plain %} declares text/plain
        {% block html %} declares text/html

    Legacy behaviour loads from:
        Subjects for email templates can be configured in one of two ways:

        * If you are using internationalisation, you can simply create entries for
          "<template_name> email subject" as a msgid in your PO file

        * Using a dictionary in settings.py, TEMPLATED_EMAIL_DJANGO_SUBJECTS,
          for e.g.:
          TEMPLATED_EMAIL_DJANGO_SUBJECTS = {
            'welcome':'Welcome to my website',
          }

    Subjects are templatable using the context, i.e. A subject
    that resolves to 'Welcome to my website, %(username)s', requires that
    the context passed in to the send() method contains 'username' as one
    of it's keys
    """

    def __init__(self, fail_silently=False,
                 template_prefix=None, template_suffix=None, **kwargs):
        self.template_prefix = template_prefix or getattr(settings, 'TEMPLATED_EMAIL_TEMPLATE_DIR', 'templated_email/')
        self.template_suffix = template_suffix or getattr(settings, 'TEMPLATED_EMAIL_FILE_EXTENSION', 'email')

    def attach_inline_images(self, message, context):
        for value in context.values():
            if isinstance(value, InlineImage):
                value.attach_to_message(message)

    def host_inline_image(self, inline_image):
        from templated_email.urls import app_name
        md5sum = hashlib.md5(inline_image.content).hexdigest()

        filename = inline_image.filename
        filename = app_name + '/' + md5sum + filename
        if not default_storage.exists(filename):
            filename = default_storage.save(filename,
                                            BytesIO(inline_image.content))
        return default_storage.url(filename)

    def _render_email(self, template_name, context,
                      template_dir=None, file_extension=None):
        response = {}
        errors = {}
        render_context = Context(context, autoescape=False)

        file_extension = file_extension or self.template_suffix
        if file_extension.startswith('.'):
            file_extension = file_extension[1:]
        template_extension = '.%s' % file_extension

        if isinstance(template_name, (tuple, list, )):
            prefixed_templates = template_name
        else:
            prefixed_templates = [template_name]

        full_template_names = []
        for one_prefixed_template in prefixed_templates:
            one_full_template_name = ''.join((template_dir or self.template_prefix, one_prefixed_template))
            if not one_full_template_name.endswith(template_extension):
                one_full_template_name += template_extension
            full_template_names.append(one_full_template_name)

        for part in ['subject', 'html', 'plain']:
            try:
                response[part] = render_block_to_string(full_template_names, part, render_context)
            except BlockNotFound as error:
                errors[part] = error

        if response == {}:
            raise EmailRenderException("Couldn't render email parts. Errors: %s"
                                       % errors)

        return response

    def get_email_message(self, template_name, context, from_email=None, to=None,
                          cc=None, bcc=None, headers=None,
                          template_prefix=None, template_suffix=None,
                          template_dir=None, file_extension=None,
                          attachments=None, create_link=False):

        if create_link:
            email_uuid = uuid.uuid4()
            link_context = dict(context)
            context['email_uuid'] = email_uuid.hex
            for key, value in context.items():
                if isinstance(value, InlineImage):
                    link_context[key] = self.host_inline_image(value)

        EmailMessage = get_emailmessage_klass()
        EmailMultiAlternatives = get_emailmultialternatives_klass()
        parts = self._render_email(template_name, context,
                                   template_prefix or template_dir,
                                   template_suffix or file_extension)
        plain_part = 'plain' in parts
        html_part = 'html' in parts

        if create_link and html_part:
            static_html_part = self._render_email(
                template_name, link_context,
                template_prefix or template_dir,
                template_suffix or file_extension)['html']
            from templated_email.models import SavedEmail
            SavedEmail.objects.create(content=static_html_part, uuid=email_uuid)

        if 'subject' in parts:
            subject = parts['subject']
        else:
            subject_dict = getattr(settings, 'TEMPLATED_EMAIL_DJANGO_SUBJECTS', {})
            if isinstance(template_name, (list, tuple)):
                for template in template_name:
                    if template in subject_dict:
                        subject_template = subject_dict[template]
                        break
                else:
                    subject_template = _('%s email subject' % template_name[0])
            else:
                subject_template = subject_dict.get(template_name,
                                                    _('%s email subject' % template_name))
            subject = subject_template % context
        subject = subject.strip('\n\r')  # strip newlines from subject

        if not plain_part:
            plain_part = self._generate_plain_part(parts)

        if plain_part and not html_part:
            e = EmailMessage(
                subject,
                parts['plain'],
                from_email,
                to,
                cc=cc,
                bcc=bcc,
                headers=headers,
                attachments=attachments,
            )

        elif html_part and not plain_part:
            e = EmailMessage(
                subject,
                parts['html'],
                from_email,
                to,
                cc=cc,
                bcc=bcc,
                headers=headers,
                attachments=attachments,
            )
            e.content_subtype = 'html'

        elif plain_part and html_part:
            e = EmailMultiAlternatives(
                subject,
                parts['plain'],
                from_email,
                to,
                cc=cc,
                bcc=bcc,
                headers=headers,
                attachments=attachments,
            )
            e.attach_alternative(parts['html'], 'text/html')

        else:
            raise EmailRenderException("Please specify at a plain and/or html block.")

        self.attach_inline_images(e, context)
        return e

    def _generate_plain_part(self, parts):
        """
        Depending on some settings, generate a plain part from the HTML part.

        The user can choose a custom "plain function" that takes an argument
        of the HTML part and returns the plain text. By default this is
        "html2text.html2text".
        """
        html_part = 'html' in parts
        auto_plain = getattr(settings, 'TEMPLATED_EMAIL_AUTO_PLAIN', True)
        plain_func = getattr(settings, 'TEMPLATED_EMAIL_PLAIN_FUNCTION', None)

        if not auto_plain:
            return

        if not html_part:
            return

        if not plain_func and html2text:
            plain_func = html2text.html2text

        if not plain_func:
            return

        parts['plain'] = plain_func(parts['html'])
        return True

    def send(self, template_name, from_email, recipient_list, context,
             cc=None, bcc=None,
             fail_silently=False,
             headers=None,
             template_prefix=None, template_suffix=None,
             template_dir=None, file_extension=None,
             auth_user=None, auth_password=None,
             connection=None, attachments=None,
             create_link=False, **kwargs):

        connection = connection or get_connection(username=auth_user,
                                                  password=auth_password,
                                                  fail_silently=fail_silently)

        e = self.get_email_message(template_name, context, from_email=from_email,
                                   to=recipient_list, cc=cc, bcc=bcc, headers=headers,
                                   template_prefix=template_prefix,
                                   template_suffix=template_suffix,
                                   template_dir=template_dir,
                                   file_extension=file_extension,
                                   attachments=attachments,
                                   create_link=create_link)

        e.connection = connection

        try:
            e.send(fail_silently)
        except NameError:
            raise EmailRenderException("Couldn't render plain or html parts")

        return e.extra_headers.get('Message-Id', None)
