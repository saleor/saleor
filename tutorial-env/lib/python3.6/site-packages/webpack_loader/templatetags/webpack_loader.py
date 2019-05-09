from django import template, VERSION
from django.conf import settings
from django.utils.safestring import mark_safe

from .. import utils

register = template.Library()


@register.simple_tag
def render_bundle(bundle_name, extension=None, config='DEFAULT', attrs=''):
    tags = utils.get_as_tags(bundle_name, extension=extension, config=config, attrs=attrs)
    return mark_safe('\n'.join(tags))


@register.simple_tag
def webpack_static(asset_name, config='DEFAULT'):
    return utils.get_static(asset_name, config=config)


assignment_tag = register.simple_tag if VERSION >= (1, 9) else register.assignment_tag
@assignment_tag
def get_files(bundle_name, extension=None, config='DEFAULT'):
    """
    Returns all chunks in the given bundle.
    Example usage::

        {% get_files 'editor' 'css' as editor_css_chunks %}
        CKEDITOR.config.contentsCss = '{{ editor_css_chunks.0.publicPath }}';

    :param bundle_name: The name of the bundle
    :param extension: (optional) filter by extension
    :param config: (optional) the name of the configuration
    :return: a list of matching chunks
    """
    return utils.get_files(bundle_name, extension=extension, config=config)
