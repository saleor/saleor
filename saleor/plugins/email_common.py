from dataclasses import dataclass
from email.headerregistry import Address
from typing import Optional

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail.backends.smtp import EmailBackend
from templated_email import TemplateBackend


@dataclass
class EmailConfig:
    host: Optional[str] = None
    port: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    sender_name: Optional[str] = None
    sender_address: Optional[str] = None
    use_tls: bool = False
    use_ssl: bool = False


def send_email(config: EmailConfig, recipient_list, template_name, context):
    sender_name = config.sender_name
    sender_address = config.sender_address
    if not sender_address or not sender_name:
        # TODO when we deprecate the default mail config from Site, we can drop this if
        # and require the sender's data as a plugin input.
        site = Site.objects.get_current()
        sender_name = sender_name or site.settings.default_mail_sender_name
        sender_address = sender_address or site.settings.default_mail_sender_address
        sender_address = sender_address or settings.DEFAULT_FROM_EMAIL

    from_email = str(Address(sender_name, addr_spec=sender_address))
    email_backend = EmailBackend(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        use_ssl=config.use_ssl,
        use_tls=config.use_tls,
    )
    template_backend = TemplateBackend()
    template_backend.send(
        from_email=from_email,
        connection=email_backend,
        template_name=template_name,
        recipient_list=recipient_list,
        context=context,
    )
    # TODO the template mail will be replaced by the send_mail whith rendered msg by
    # staff user

    # send_mail(
    #     subject,
    #     message,
    #     from_email,
    #     recipient_list,
    #     connection=email_backend
    # )


def validate_email_config(config: EmailConfig):
    email_backend = EmailBackend(
        host=config.host,
        port=config.port,
        username=config.username,
        password=config.password,
        use_ssl=config.use_ssl,
        use_tls=config.use_tls,
        fail_silently=False,
    )
    try:
        email_backend.open()
    except Exception:
        raise
    finally:
        email_backend.close()
