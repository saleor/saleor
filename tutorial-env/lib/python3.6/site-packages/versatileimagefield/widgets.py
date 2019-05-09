from __future__ import unicode_literals

import django
from django.forms.widgets import ClearableFileInput, HiddenInput, MultiWidget, Select
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

CENTERPOINT_CHOICES = (
    ('0.0x0.0', 'Top Left'),
    ('0.0x0.5', 'Top Center'),
    ('0.0x1.0', 'Top Right'),
    ('0.5x0.0', 'Middle Left'),
    ('0.5x0.5', 'Middle Center'),
    ('0.5x1.0', 'Middle Right'),
    ('1.0x0.0', 'Bottom Left'),
    ('1.0x0.5', 'Bottom Center'),
    ('1.0x1.0', 'Bottom Right'),
)


class ClearableFileInputWithImagePreview(ClearableFileInput):

    has_template_widget_rendering = django.VERSION >= (1, 11)
    template_name = 'versatileimagefield/forms/widgets/versatile_image.html'

    def get_hidden_field_id(self, name):
        i = name.rindex('_')
        return "id_%s_%d" % (name[:i], int(name[i + 1:]) + 1)

    def image_preview_id(self, name):
        """Given the name of the image preview tag, return the HTML id for it."""
        return name + '_imagepreview'

    def get_ppoi_id(self, name):
        """Given the name of the primary point of interest tag, return the HTML id for it."""
        return name + '_ppoi'

    def get_point_stage_id(self, name):
        return name + '_point-stage'

    def render(self, name, value, attrs=None, renderer=None):
        """
        Render the widget as an HTML string.

        Overridden here to support Django < 1.11.
        """
        if self.has_template_widget_rendering:
            return super(ClearableFileInputWithImagePreview, self).render(
                name, value, attrs=attrs, renderer=renderer
            )
        else:
            context = self.get_context(name, value, attrs)
            return render_to_string(self.template_name, context)

    def get_sized_url(self, value):
        """Do not fail completely on invalid images"""
        try:
            # Ensuring admin preview thumbnails are created and available
            value.create_on_demand = True
            return value.thumbnail['300x300']
        except Exception:
            # Do not be overly specific with exceptions; we'd rather show no
            # thumbnail than crash when showing the widget.
            return None

    def get_context(self, name, value, attrs):
        """Get the context to render this widget with."""
        if self.has_template_widget_rendering:
            context = super(ClearableFileInputWithImagePreview, self).get_context(name, value, attrs)
        else:
            # Build the context manually.
            context = {}
            context['widget'] = {
                'name': name,
                'is_hidden': self.is_hidden,
                'required': self.is_required,
                'value': self._format_value(value),
                'attrs': self.build_attrs(self.attrs, attrs),
                'template_name': self.template_name,
                'type': self.input_type,
            }

        # It seems Django 1.11's ClearableFileInput doesn't add everything to the 'widget' key, so we can't use it
        # in MultiWidget. Add it manually here.
        checkbox_name = self.clear_checkbox_name(name)
        checkbox_id = self.clear_checkbox_id(checkbox_name)

        context['widget'].update({
            'checkbox_name': checkbox_name,
            'checkbox_id': checkbox_id,
            'is_initial': self.is_initial(value),
            'input_text': self.input_text,
            'initial_text': self.initial_text,
            'clear_checkbox_label': self.clear_checkbox_label,
        })

        if value and hasattr(value, "url"):
            context['widget'].update({
                'hidden_field_id': self.get_hidden_field_id(name),
                'point_stage_id': self.get_point_stage_id(name),
                'ppoi_id': self.get_ppoi_id(name),
                'sized_url': self.get_sized_url(value),
                'image_preview_id': self.image_preview_id(name),
            })

        return context

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build an attribute dictionary."""
        attrs = base_attrs.copy()
        if extra_attrs is not None:
            attrs.update(extra_attrs)
        return attrs


class SizedImageCenterpointWidgetMixIn(object):

    def decompress(self, value):
        return [value, 'x'.join(str(num) for num in value.ppoi)] if value else [None, None]


class VersatileImagePPOISelectWidget(SizedImageCenterpointWidgetMixIn, MultiWidget):

    def __init__(self, widgets=None, attrs=None):
        widgets = [
            ClearableFileInput(attrs=None),
            Select(attrs=attrs, choices=CENTERPOINT_CHOICES)
        ]
        super(VersatileImagePPOISelectWidget, self).__init__(widgets, attrs)


class VersatileImagePPOIClickWidget(SizedImageCenterpointWidgetMixIn, MultiWidget):

    def __init__(self, widgets=None, attrs=None, image_preview_template=None):
        widgets = (
            ClearableFileInputWithImagePreview(attrs={'class': 'file-chooser'}),
            HiddenInput(attrs={'class': 'ppoi-input'})
        )
        super(VersatileImagePPOIClickWidget, self).__init__(widgets, attrs)

    class Media:
        css = {
            'all': ('versatileimagefield/css/versatileimagefield.css',),
        }
        js = ('versatileimagefield/js/versatileimagefield.js',)

    def render(self, name, value, attrs=None, renderer=None):
        rendered = super(VersatileImagePPOIClickWidget, self).render(name, value, attrs=attrs)
        return mark_safe('<div class="versatileimagefield">{}</div>'.format(rendered))


class SizedImageCenterpointClickDjangoAdminWidget(VersatileImagePPOIClickWidget):

    class Media:
        css = {
            'all': ('versatileimagefield/css/versatileimagefield-djangoadmin.css',),
        }


class Bootstrap3ClearableFileInputWithImagePreview(ClearableFileInputWithImagePreview):
    """A Bootstrap 3 version of the clearable file input with image preview."""

    template_name = 'versatileimagefield/forms/widgets/versatile_image_bootstrap.html'


class SizedImageCenterpointClickBootstrap3Widget(VersatileImagePPOIClickWidget):

    def __init__(self, widgets=None, attrs=None):
        widgets = (
            Bootstrap3ClearableFileInputWithImagePreview(attrs={'class': 'file-chooser'}),
            HiddenInput(attrs={'class': 'ppoi-input'})
        )
        super(VersatileImagePPOIClickWidget, self).__init__(widgets, attrs)

    class Media:
        css = {
            'all': ('versatileimagefield/css/versatileimagefield-bootstrap3.css',),
        }
