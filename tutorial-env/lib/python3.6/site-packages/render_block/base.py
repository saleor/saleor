from __future__ import absolute_import

from django.template import loader
from django.template.backends.django import Template as DjangoTemplate
try:
    from django.template.backends.jinja2 import Template as Jinja2Template
except ImportError:
    # Most likely Jinja2 isn't installed, in that case just create a class since
    # we always want it to be false anyway.
    class Jinja2Template(object):
        pass

from render_block.django import django_render_block
from render_block.exceptions import BlockNotFound, UnsupportedEngine


def render_block_to_string(template_name, block_name, context=None):
    """
    Loads the given template_name and renders the given block with the given
    dictionary as context. Returns a string.

        template_name
            The name of the template to load and render. If it's a list of
            template names, Django uses select_template() instead of
            get_template() to find the template.
    """

    # Like render_to_string, template_name can be a string or a list/tuple.
    if isinstance(template_name, (tuple, list)):
        t = loader.select_template(template_name)
    else:
        t = loader.get_template(template_name)

    # Create the context instance.
    context = context or {}

    # The Django backend.
    if isinstance(t, DjangoTemplate):
        return django_render_block(t, block_name, context)

    elif isinstance(t, Jinja2Template):
        from render_block.jinja2 import jinja2_render_block
        return jinja2_render_block(t, block_name, context)

    else:
        raise UnsupportedEngine(
            'Can only render blocks from the Django template backend.')
