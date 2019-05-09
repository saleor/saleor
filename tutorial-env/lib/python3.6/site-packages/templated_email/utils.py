from functools import partial
from email.utils import unquote
from email.mime.image import MIMEImage

from django.core.mail import make_msgid
from django.utils.module_loading import import_string
from django.conf import settings

import six


def _get_klass_from_config(config_variable, default):
    klass_path = getattr(settings, config_variable, default)
    if isinstance(klass_path, six.string_types):
        klass_path = import_string(klass_path)

    return klass_path


get_emailmessage_klass = partial(
    _get_klass_from_config,
    'TEMPLATED_EMAIL_EMAIL_MESSAGE_CLASS',
    'django.core.mail.EmailMessage'
)

get_emailmultialternatives_klass = partial(
    _get_klass_from_config,
    'TEMPLATED_EMAIL_EMAIL_MULTIALTERNATIVES_CLASS',
    'django.core.mail.EmailMultiAlternatives',
)


class InlineImage(object):

    def __init__(self, filename, content, subtype=None, domain=None):
        self.filename = filename
        self._content = content
        self.subtype = subtype
        self.domain = domain
        self._content_id = None

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, value):
        self._content_id = None
        self._content = value

    def attach_to_message(self, message):
        if not self._content_id:
            self.generate_cid()
        image = MIMEImage(self.content, self.subtype)
        image.add_header('Content-Disposition', 'inline', filename=self.filename)
        image.add_header('Content-ID', self._content_id)
        message.attach(image)

    def generate_cid(self):
        self._content_id = make_msgid('img', self.domain)

    def __str__(self):
        if not self._content_id:
            self.generate_cid()
        return 'cid:' + unquote(self._content_id)
