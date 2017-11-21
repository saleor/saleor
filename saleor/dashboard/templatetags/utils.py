from __future__ import unicode_literals

from versatileimagefield.widgets import VersatileImagePPOIClickWidget
from ..product.widgets import ImagePreviewWidget

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from django.template import Library
from ...product.utils import get_margin_for_variant, get_variant_costs_data

register = Library()


@register.simple_tag(takes_context=True)
def construct_get_query(context, **params):
    request_get = context['request'].GET.dict()
    if not (request_get or params):
        return ''
    all_params = {}
    all_params.update(request_get)
    all_params.update(params)
    all_params.update(context.get('default_pagination_params', {}))
    return '?' + urlencode(all_params)


@register.filter
def is_versatile_image_ppoi_click_widget(field):
    '''
    This filter checks if image field widget is used when user wants to edit
    existing product image.
    '''
    return isinstance(field.field.widget, VersatileImagePPOIClickWidget)


@register.filter
def is_image_preview_widget(field):
    '''
    This filter checks if image field widget is used when user wants to add new
    product image.
    '''
    return isinstance(field.field.widget, ImagePreviewWidget)


@register.inclusion_tag('dashboard/product/product_variant/_image_select.html')
def render_image_choice(field):
    choices = zip(field, field.field.queryset)
    return {'field': field, 'choices_with_images': choices}


@register.inclusion_tag('dashboard/includes/_pagination.html',
                        takes_context=True)
def paginate(context, page_obj, num_of_pages=5):
    context['page_obj'] = page_obj
    context['n_forward'] = num_of_pages + 1
    context['n_backward'] = -num_of_pages - 1
    context['next_section'] = (2 * num_of_pages) + 1
    context['previous_section'] = (-2 * num_of_pages) - 1
    return context


@register.simple_tag
def margin_for_variant(stock):
    return get_margin_for_variant(stock)


@register.simple_tag
def margins_for_variant(variant):
    margins = get_variant_costs_data(variant)['margins']
    return margins


@register.inclusion_tag('dashboard/includes/_filters.html', takes_context=True)
def add_filters(context, filter_set):
    chips = filter_set.get_chips()
    context['chips'] = chips
    return context
