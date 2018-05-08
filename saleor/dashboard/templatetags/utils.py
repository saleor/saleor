from __future__ import unicode_literals

from json import dumps
from urllib.parse import urlencode

from django import forms
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.template import Library
from django_filters.fields import RangeField
from versatileimagefield.widgets import VersatileImagePPOIClickWidget

from ...product.utils.costs import (
    get_margin_for_variant, get_variant_costs_data)
from ..product.widgets import ImagePreviewWidget
from .chips import (
    handle_default, handle_multiple_choice, handle_multiple_model_choice,
    handle_nullboolean, handle_range, handle_single_choice,
    handle_single_model_choice)

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
    """Check if image field widget is used when editing a product image."""
    return isinstance(field.field.widget, VersatileImagePPOIClickWidget)


@register.filter
def is_image_preview_widget(field):
    """Check if image field widget is used when adding a product image."""
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
    return get_variant_costs_data(variant).margins


@register.inclusion_tag('dashboard/includes/_filters.html', takes_context=True)
def filters(context, filter_set, sort_by_filter_name='sort_by'):
    """Render the filtering template based on the filter set."""
    chips = []
    request_get = context['request'].GET.copy()
    for filter_name in filter_set.form.cleaned_data.keys():
        if filter_name == sort_by_filter_name:
            # Skip processing of sort_by filter, as it's rendered differently
            continue

        field = filter_set.form[filter_name]
        if field.value() not in ['', None]:
            if isinstance(field.field, forms.NullBooleanField):
                items = handle_nullboolean(field, request_get)
            elif isinstance(field.field, forms.ModelMultipleChoiceField):
                items = handle_multiple_model_choice(field, request_get)
            elif isinstance(field.field, forms.MultipleChoiceField):
                items = handle_multiple_choice(field, request_get)
            elif isinstance(field.field, forms.ModelChoiceField):
                items = handle_single_model_choice(field, request_get)
            elif isinstance(field.field, forms.ChoiceField):
                items = handle_single_choice(field, request_get)
            elif isinstance(field.field, RangeField):
                items = handle_range(field, request_get)
            else:
                items = handle_default(field, request_get)
            chips.extend(items)
    return {
        'chips': chips, 'filter': filter_set,
        'sort_by': request_get.get(sort_by_filter_name, None)}


@register.simple_tag(takes_context=True)
def serialize_messages(context):
    """Serialize django.contrib.messages to JSON."""
    messages = context.get('messages', [])
    data = {}
    for i, message in enumerate(messages):
        data[i] = str(message)
    return dumps(data)


@register.inclusion_tag(
    'dashboard/includes/_sorting_header.html', takes_context=True)
def sorting_header(context, field, label, is_wide=False):
    """Render a table sorting header."""
    request = context['request']
    request_get = request.GET.copy()
    sort_by = request_get.get('sort_by')

    # path to icon indicating applied sorting
    sorting_icon = ''

    # flag which determines if active sorting is on field
    is_active = False

    if sort_by:
        if field == sort_by:
            is_active = True
            # enable ascending sort
            # new_sort_by is used to construct a link with already toggled
            # sort_by value
            new_sort_by = '-%s' % field
            sorting_icon = static('/images/arrow-up-icon.svg')
        else:
            # enable descending sort
            new_sort_by = field
            if field == sort_by.strip('-'):
                is_active = True
                sorting_icon = static('/images/arrow-down-icon.svg')
    else:
        new_sort_by = field

    request_get['sort_by'] = new_sort_by
    return {
        'url': '%s?%s' % (request.path, request_get.urlencode()),
        'is_active': is_active, 'sorting_icon': sorting_icon, 'label': label,
        'is_wide': is_wide}
