from __future__ import unicode_literals
from django.template import Library
from django.forms.fields import NullBooleanField, ChoiceField
from django.forms.models import ModelMultipleChoiceField
from django_filters.fields import RangeField
from versatileimagefield.widgets import VersatileImagePPOIClickWidget

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from ...product.utils import get_margin_for_variant, get_variant_costs_data
from ..chips import (handle_nullboolean, handle_default, handle_multiplechoice,
                     handle_range, handle_choice)
from ..product.widgets import ImagePreviewWidget

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
    chips = []
    data = filter_set.form.cleaned_data
    for key in data.keys():
        if key == 'sort_by':
            continue
        field = filter_set.form[key]
        if field.value() not in ['', None]:
            if isinstance(field.field, NullBooleanField):
                chips = handle_nullboolean(field, chips)
            elif isinstance(field.field, ModelMultipleChoiceField):
                field_data = {str(o.pk): str(o) for o in data[key]}
                chips = handle_multiplechoice(field, chips, field_data)
            elif isinstance(field.field, RangeField):
                chips = handle_range(field, chips)
            elif isinstance(field.field, ChoiceField):
                chips = handle_choice(field, chips)
            else:
                chips = handle_default(field, chips)
    filter_context = {
        'chips': chips,
        'filter': filter_set
    }
    return filter_context
