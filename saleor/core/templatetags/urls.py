from django import template
from django.conf import settings
from django.urls import reverse, translate_url as django_translate_url

register = template.Library()


@register.simple_tag
def build_absolute_uri(request, location):
    return request.build_absolute_uri(location)


@register.simple_tag
def translate_url(url, lang_code):
    return django_translate_url(url, lang_code)


@register.simple_tag
def privacy_page_url():
    return reverse(
        'page:details', kwargs={'settings.PRIVACY_PAGE_SLUG'})


def get_internal_page_slug(internal_name):
    """Retrieve the slug of an internal page name.

    This mechanism is there to allow user to customize internal pages' slug
    that Saleor is depending on without breaking some features.

    This function, depends on the settings key `INTERNAL_PAGES`, which,
    is has the following syntax:

      Dict[InternalName<str>, PageSlug<str>]

    :raise ValueError:
      Raises a ValueError if the internal page is not registered (missing).
      This should not happen if the user didn't touch the configuration,
      as the default settings should be valid.
      But may happen if the user do changes the settings key `INTERNAL_PAGES`,
      as the contains the relations.
    """
    internal_pages = settings.INTERNAL_PAGES

    if internal_name in internal_pages:
        return internal_pages[internal_name]

    raise ValueError((
        '\'{}\' is not a know internal page name. '
        'Please check the \'INTERNAL_PAGES\' settings key if you edited it.'
    ).format(internal_name))


@register.simple_tag
def get_internal_page_url(internal_name):
    """Returns the page URL of an internal page
    by using its associated slug.
    """
    slug = get_internal_page_slug(internal_name)
    return reverse('page:details', kwargs={'slug': slug})
