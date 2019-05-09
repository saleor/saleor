import datetime
import warnings

from django.conf import settings
from django.contrib.admin.templatetags.admin_list import (
    result_hidden_fields, result_headers)
from django.contrib.admin.templatetags.admin_urls import add_preserved_filters
from django.contrib.admin.utils import (
    display_for_field, display_for_value, lookup_field)
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.template import Library
from django.urls import NoReverseMatch
try:
    from django.utils.deprecation import RemovedInDjango20Warning
except ImportError:
    RemovedInDjango20Warning = RuntimeWarning
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import get_language_bidi
from django.contrib.admin.templatetags.admin_list import _coerce_field_name


register = Library()


MPTT_ADMIN_LEVEL_INDENT = getattr(settings, 'MPTT_ADMIN_LEVEL_INDENT', 10)
IS_GRAPPELLI_INSTALLED = True if 'grappelli' in settings.INSTALLED_APPS else False


###
# Ripped from contrib.admin's (1.10) items_for_result tag.
# The only difference is we're indenting nodes according to their level.
def mptt_items_for_result(cl, result, form):
    """
    Generates the actual list of data.
    """

    def link_in_col(is_first, field_name, cl):
        if cl.list_display_links is None:
            return False
        if is_first and not cl.list_display_links:
            return True
        return field_name in cl.list_display_links

    first = True
    pk = cl.lookup_opts.pk.attname

    # #### MPTT ADDITION START
    # figure out which field to indent
    mptt_indent_field = getattr(cl.model_admin, 'mptt_indent_field', None)
    if not mptt_indent_field:
        for field_name in cl.list_display:
            try:
                f = cl.lookup_opts.get_field(field_name)
            except models.FieldDoesNotExist:
                if (mptt_indent_field is None and
                        field_name != 'action_checkbox'):
                    mptt_indent_field = field_name
            else:
                # first model field, use this one
                mptt_indent_field = field_name
                break

    # figure out how much to indent
    mptt_level_indent = getattr(cl.model_admin, 'mptt_level_indent', MPTT_ADMIN_LEVEL_INDENT)
    # #### MPTT ADDITION END

    for field_index, field_name in enumerate(cl.list_display):
        # #### MPTT SUBSTITUTION START
        empty_value_display = cl.model_admin.get_empty_value_display()
        # #### MPTT SUBSTITUTION END
        row_classes = ['field-%s' % _coerce_field_name(field_name, field_index)]
        try:
            f, attr, value = lookup_field(field_name, result, cl.model_admin)
        except ObjectDoesNotExist:
            result_repr = empty_value_display
        else:
            empty_value_display = getattr(attr, 'empty_value_display', empty_value_display)
            if f is None or f.auto_created:
                if field_name == 'action_checkbox':
                    row_classes = ['action-checkbox']
                allow_tags = getattr(attr, 'allow_tags', False)
                boolean = getattr(attr, 'boolean', False)
                # #### MPTT SUBSTITUTION START
                result_repr = display_for_value(value, empty_value_display, boolean)
                # #### MPTT SUBSTITUTION END
                if allow_tags:
                    warnings.warn(
                        "Deprecated allow_tags attribute used on field {}. "
                        "Use django.utils.safestring.format_html(), "
                        "format_html_join(), or mark_safe() instead.".format(field_name),
                        RemovedInDjango20Warning
                    )
                    result_repr = mark_safe(result_repr)
                if isinstance(value, (datetime.date, datetime.time)):
                    row_classes.append('nowrap')
            else:
                # #### MPTT SUBSTITUTION START
                is_many_to_one = isinstance(f.remote_field, models.ManyToOneRel)
                if is_many_to_one:
                    # #### MPTT SUBSTITUTION END
                    field_val = getattr(result, f.name)
                    if field_val is None:
                        result_repr = empty_value_display
                    else:
                        result_repr = field_val
                else:
                    # #### MPTT SUBSTITUTION START
                    result_repr = display_for_field(value, f, empty_value_display)
                    # #### MPTT SUBSTITUTION END
                if isinstance(f, (models.DateField, models.TimeField, models.ForeignKey)):
                    row_classes.append('nowrap')
        if force_text(result_repr) == '':
            result_repr = mark_safe('&nbsp;')
        row_class = mark_safe(' class="%s"' % ' '.join(row_classes))

        # #### MPTT ADDITION START
        if field_name == mptt_indent_field:
            level = getattr(result, result._mptt_meta.level_attr)
            padding_attr = mark_safe(' style="padding-%s:%spx"' % (
                'right' if get_language_bidi() else 'left',
                8 + mptt_level_indent * level))
        else:
            padding_attr = ''
        # #### MPTT ADDITION END

        # If list_display_links not defined, add the link tag to the first field
        if link_in_col(first, field_name, cl):
            table_tag = 'th' if first else 'td'
            first = False

            # Display link to the result's change_view if the url exists, else
            # display just the result's representation.
            try:
                url = cl.url_for_result(result)
            except NoReverseMatch:
                link_or_text = result_repr
            else:
                url = add_preserved_filters(
                    {'preserved_filters': cl.preserved_filters, 'opts': cl.opts}, url,
                )
                # Convert the pk to something that can be used in Javascript.
                # Problem cases are long ints (23L) and non-ASCII strings.
                if cl.to_field:
                    attr = str(cl.to_field)
                else:
                    attr = pk
                value = result.serializable_value(attr)
                if cl.is_popup:
                    opener = format_html(' data-popup-opener="{}"', value)
                else:
                    opener = ''
                link_or_text = format_html(
                    '<a href="{}"{}>{}</a>',
                    url,
                    opener,
                    result_repr)

            # #### MPTT SUBSTITUTION START
            yield format_html('<{}{}{}>{}</{}>',
                              table_tag,
                              row_class,
                              padding_attr,
                              link_or_text,
                              table_tag)
            # #### MPTT SUBSTITUTION END
        else:
            # By default the fields come from ModelAdmin.list_editable, but if we pull
            # the fields out of the form instead of list_editable custom admins
            # can provide fields on a per request basis
            if (form and field_name in form.fields and not (
                    field_name == cl.model._meta.pk.name and
                    form[cl.model._meta.pk.name].is_hidden)):
                bf = form[field_name]
                result_repr = mark_safe(force_text(bf.errors) + force_text(bf))
            # #### MPTT SUBSTITUTION START
            yield format_html('<td{}{}>{}</td>', row_class, padding_attr, result_repr)
            # #### MPTT SUBSTITUTION END
    if form and not form[cl.model._meta.pk.name].is_hidden:
        yield format_html('<td>{}</td>', force_text(form[cl.model._meta.pk.name]))


def mptt_results(cl):
    if cl.formset:
        for res, form in zip(cl.result_list, cl.formset.forms):
            yield list(mptt_items_for_result(cl, res, form))
    else:
        for res in cl.result_list:
            yield list(mptt_items_for_result(cl, res, None))


def mptt_result_list(cl):
    """
    Displays the headers and data list together
    """
    return {'cl': cl,
            'result_hidden_fields': list(result_hidden_fields(cl)),
            'result_headers': list(result_headers(cl)),
            'results': list(mptt_results(cl))}


# custom template is merely so we can strip out sortable-ness from the column headers
# Based on admin/change_list_results.html (1.3.1)
if IS_GRAPPELLI_INSTALLED:
    mptt_result_list = register.inclusion_tag(
        "admin/grappelli_mptt_change_list_results.html")(mptt_result_list)
else:
    mptt_result_list = register.inclusion_tag(
        "admin/mptt_change_list_results.html")(mptt_result_list)
