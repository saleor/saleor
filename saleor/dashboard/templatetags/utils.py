from __future__ import unicode_literals

from django import forms
from django.template import Library
from django_filters.fields import RangeField
from versatileimagefield.widgets import VersatileImagePPOIClickWidget

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode

from ...product.utils import get_margin_for_variant, get_variant_costs_data
from .chips import (
    handle_default, handle_multiple_choice, handle_multiple_model_choice,
    handle_nullboolean, handle_range, handle_single_choice,
    handle_single_model_choice)
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
def add_filters(context, filter_set, sort_by_filter_name='sort_by'):
    chips = []
    cleaned_data = filter_set.form.cleaned_data
    for filter_name in cleaned_data.keys():
        if filter_name == sort_by_filter_name:
            # Skip processing of sort_by filter, as it's rendered differently
            continue

        field = filter_set.form[filter_name]
        if field.value() not in ['', None]:
            if isinstance(field.field, forms.NullBooleanField):
                items = handle_nullboolean(field)
            elif isinstance(field.field, forms.ModelMultipleChoiceField):
                items = handle_multiple_model_choice(
                    field, cleaned_data[filter_name])
            elif isinstance(field.field, forms.MultipleChoiceField):
                items = handle_multiple_choice(
                    field, cleaned_data[filter_name])
            elif isinstance(field.field, forms.ModelChoiceField):
                items = handle_single_model_choice(
                    field, cleaned_data[filter_name])
            elif isinstance(field.field, forms.ChoiceField):
                items = handle_single_choice(field, cleaned_data[filter_name])
            elif isinstance(field.field, RangeField):
                items = handle_range(field)
            else:
                items = handle_default(field)
            chips.extend(items)

    for chip in chips:
        request = context['request'].GET.copy()
        param_values = request.getlist(chip['name'])
        all_values = {k: request.getlist(k) for k in request.keys()}
        index_of_value = param_values.index(str(chip['value']))
        del all_values[chip['name']][index_of_value]
        del chip['value']
        del chip['name']
        chip['link'] = '?' + urlencode(all_values, True)

    return {
        'chips': chips, 'filter': filter_set, 'count': filter_set.qs.count(),
        'request': context['request']}
