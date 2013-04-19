from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template
from django.template.loader_tags import BlockNode

BLOCKS = [SUBJECT, TEXT, HTML] = 'subject', 'text', 'html'  # template blocks


def send_email(address, template_name, context=None):
    """Renders template blocks and sends an email."""
    blocks = render_blocks(template_name=template_name, context=context or {})
    message = EmailMultiAlternatives(
        subject=blocks[SUBJECT],
        body=blocks[TEXT],
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[address])
    if HTML in blocks:
        message.attach_alternative(blocks[HTML], 'text/html')
    message.send()


def render_blocks(template_name, context):
    """Renders BLOCKS from template. Block needs to be a top level node."""
    context = Context(context)
    template = get_template(template_name=template_name)
    return dict((node.name, node.render(context)) for node in template
                if isinstance(node, BlockNode) and node.name in BLOCKS)
