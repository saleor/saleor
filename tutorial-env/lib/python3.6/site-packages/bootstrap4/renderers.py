# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    # If Django is set up without a database, importing this widget gives RuntimeError
    from django.contrib.auth.forms import ReadOnlyPasswordHashWidget
except RuntimeError:
    ReadOnlyPasswordHashWidget = None

from django.forms import (
    TextInput,
    PasswordInput,
    DateInput,
    FileInput,
    NumberInput,
    CheckboxInput,
    MultiWidget,
    ClearableFileInput,
    Select,
    RadioSelect,
    CheckboxSelectMultiple,
    EmailInput,
)
from django.forms.widgets import SelectDateWidget
from django.forms.forms import BaseForm, BoundField
from django.forms.formsets import BaseFormSet
from django.utils.html import conditional_escape, escape, strip_tags
from django.utils.safestring import mark_safe

from .bootstrap import get_bootstrap_setting
from .exceptions import BootstrapError
from .forms import (
    render_form,
    render_field,
    render_label,
    render_form_group,
    is_widget_with_placeholder,
    FORM_GROUP_CLASS,
)
from .text import text_value
from .utils import add_css_class, render_template_file


class BaseRenderer(object):
    """
    A content renderer
    """

    def __init__(self, *args, **kwargs):
        self.layout = kwargs.get("layout", "")
        self.form_group_class = kwargs.get("form_group_class", FORM_GROUP_CLASS)
        self.field_class = kwargs.get("field_class", "")
        self.label_class = kwargs.get("label_class", "")
        self.show_help = kwargs.get("show_help", True)
        self.show_label = kwargs.get("show_label", True)
        self.exclude = kwargs.get("exclude", "")

        self.set_placeholder = kwargs.get("set_placeholder", True)
        self.size = self.parse_size(kwargs.get("size", ""))
        self.horizontal_label_class = kwargs.get(
            "horizontal_label_class", get_bootstrap_setting("horizontal_label_class")
        )
        self.horizontal_field_class = kwargs.get(
            "horizontal_field_class", get_bootstrap_setting("horizontal_field_class")
        )

    def parse_size(self, size):
        size = text_value(size).lower().strip()
        if size in ("sm", "small"):
            return "small"
        if size in ("lg", "large"):
            return "large"
        if size in ("md", "medium", ""):
            return "medium"
        raise BootstrapError(
            'Invalid value "%s" for parameter "size" (expected "sm", "md", "lg" or "").' % size
        )

    def get_size_class(self, prefix="form-control"):
        if self.size == "small":
            return prefix + "-sm"
        if self.size == "large":
            return prefix + "-lg"
        return ""

    def _render(self):
        return ""

    def render(self):
        return mark_safe(self._render())


class FormsetRenderer(BaseRenderer):
    """
    Default formset renderer
    """

    def __init__(self, formset, *args, **kwargs):
        if not isinstance(formset, BaseFormSet):
            raise BootstrapError('Parameter "formset" should contain a valid Django Formset.')
        self.formset = formset
        super(FormsetRenderer, self).__init__(*args, **kwargs)

    def render_management_form(self):
        return text_value(self.formset.management_form)

    def render_form(self, form, **kwargs):
        return render_form(form, **kwargs)

    def render_forms(self):
        rendered_forms = []
        for form in self.formset.forms:
            rendered_forms.append(
                self.render_form(
                    form,
                    layout=self.layout,
                    form_group_class=self.form_group_class,
                    field_class=self.field_class,
                    label_class=self.label_class,
                    show_label=self.show_label,
                    show_help=self.show_help,
                    exclude=self.exclude,
                    set_placeholder=self.set_placeholder,
                    size=self.size,
                    horizontal_label_class=self.horizontal_label_class,
                    horizontal_field_class=self.horizontal_field_class,
                )
            )
        return "\n".join(rendered_forms)

    def get_formset_errors(self):
        return self.formset.non_form_errors()

    def render_errors(self):
        formset_errors = self.get_formset_errors()
        if formset_errors:
            return render_template_file(
                "bootstrap4/form_errors.html",
                context={"errors": formset_errors, "form": self.formset, "layout": self.layout},
            )
        return ""

    def _render(self):
        return "{}{}{}".format(
            self.render_errors(), self.render_management_form(), self.render_forms()
        )


class FormRenderer(BaseRenderer):
    """
    Default form renderer
    """

    def __init__(self, form, *args, **kwargs):
        if not isinstance(form, BaseForm):
            raise BootstrapError('Parameter "form" should contain a valid Django Form.')
        self.form = form
        super(FormRenderer, self).__init__(*args, **kwargs)
        self.error_css_class = kwargs.get("error_css_class", None)
        self.required_css_class = kwargs.get("required_css_class", None)
        self.bound_css_class = kwargs.get("bound_css_class", None)

    def render_fields(self):
        rendered_fields = []
        for field in self.form:
            rendered_fields.append(
                render_field(
                    field,
                    layout=self.layout,
                    form_group_class=self.form_group_class,
                    field_class=self.field_class,
                    label_class=self.label_class,
                    show_label=self.show_label,
                    show_help=self.show_help,
                    exclude=self.exclude,
                    set_placeholder=self.set_placeholder,
                    size=self.size,
                    horizontal_label_class=self.horizontal_label_class,
                    horizontal_field_class=self.horizontal_field_class,
                    error_css_class=self.error_css_class,
                    required_css_class=self.required_css_class,
                    bound_css_class=self.bound_css_class,
                )
            )
        return "\n".join(rendered_fields)

    def get_fields_errors(self):
        form_errors = []
        for field in self.form:
            if not field.is_hidden and field.errors:
                form_errors += field.errors
        return form_errors

    def render_errors(self, type="all"):
        form_errors = None
        if type == "all":
            form_errors = self.get_fields_errors() + self.form.non_field_errors()
        elif type == "fields":
            form_errors = self.get_fields_errors()
        elif type == "non_fields":
            form_errors = self.form.non_field_errors()

        if form_errors:
            return render_template_file(
                "bootstrap4/form_errors.html",
                context={
                    "errors": form_errors,
                    "form": self.form,
                    "layout": self.layout,
                    "type": type,
                },
            )

        return ""

    def _render(self):
        return self.render_errors() + self.render_fields()


class FieldRenderer(BaseRenderer):
    """
    Default field renderer
    """

    # These widgets will not be wrapped in a form-control class
    WIDGETS_NO_FORM_CONTROL = (CheckboxInput, RadioSelect, CheckboxSelectMultiple, FileInput)

    def __init__(self, field, *args, **kwargs):
        if not isinstance(field, BoundField):
            raise BootstrapError('Parameter "field" should contain a valid Django BoundField.')
        self.field = field
        super(FieldRenderer, self).__init__(*args, **kwargs)

        self.widget = field.field.widget
        self.is_multi_widget = isinstance(field.field.widget, MultiWidget)
        self.initial_attrs = self.widget.attrs.copy()
        self.field_help = (
            text_value(mark_safe(field.help_text)) if self.show_help and field.help_text else ""
        )
        self.field_errors = [conditional_escape(text_value(error)) for error in field.errors]

        if "placeholder" in kwargs:
            # Find the placeholder in kwargs, even if it's empty
            self.placeholder = kwargs["placeholder"]
        elif get_bootstrap_setting("set_placeholder"):
            # If not found, see if we set the label
            self.placeholder = field.label
        else:
            # Or just set it to empty
            self.placeholder = ""
        if self.placeholder:
            self.placeholder = text_value(self.placeholder)

        self.addon_before = kwargs.get("addon_before", self.widget.attrs.pop("addon_before", ""))
        self.addon_after = kwargs.get("addon_after", self.widget.attrs.pop("addon_after", ""))
        self.addon_before_class = kwargs.get(
            "addon_before_class", self.widget.attrs.pop("addon_before_class", "input-group-text")
        )
        self.addon_after_class = kwargs.get(
            "addon_after_class", self.widget.attrs.pop("addon_after_class", "input-group-text")
        )

        # These are set in Django or in the global BOOTSTRAP4 settings, and
        # they can be overwritten in the template
        error_css_class = kwargs.get("error_css_class", None)
        required_css_class = kwargs.get("required_css_class", None)
        bound_css_class = kwargs.get("bound_css_class", None)
        if error_css_class is not None:
            self.error_css_class = error_css_class
        else:
            self.error_css_class = getattr(
                field.form, "error_css_class", get_bootstrap_setting("error_css_class")
            )
        if required_css_class is not None:
            self.required_css_class = required_css_class
        else:
            self.required_css_class = getattr(
                field.form, "required_css_class", get_bootstrap_setting("required_css_class")
            )
        if bound_css_class is not None:
            self.success_css_class = bound_css_class
        else:
            self.success_css_class = getattr(
                field.form, "bound_css_class", get_bootstrap_setting("success_css_class")
            )

        # If the form is marked as form.empty_permitted, do not set required class
        if self.field.form.empty_permitted:
            self.required_css_class = ""

    def restore_widget_attrs(self):
        self.widget.attrs = self.initial_attrs.copy()

    def add_class_attrs(self, widget=None):
        if widget is None:
            widget = self.widget
        classes = widget.attrs.get("class", "")
        if ReadOnlyPasswordHashWidget is not None and isinstance(
            widget, ReadOnlyPasswordHashWidget
        ):
            # Render this is a static control
            classes = add_css_class(classes, "form-control-static", prepend=True)
        elif not isinstance(widget, self.WIDGETS_NO_FORM_CONTROL):
            classes = add_css_class(classes, "form-control", prepend=True)
            # For these widget types, add the size class here
            classes = add_css_class(classes, self.get_size_class())
        elif isinstance(widget, CheckboxInput):
            classes = add_css_class(classes, "form-check-input", prepend=True)

        if self.field.errors:
            if self.error_css_class:
                classes = add_css_class(classes, self.error_css_class)
        else:
            if self.field.form.is_bound:
                classes = add_css_class(classes, self.success_css_class)

        widget.attrs["class"] = classes

    def add_placeholder_attrs(self, widget=None):
        if widget is None:
            widget = self.widget
        placeholder = widget.attrs.get("placeholder", self.placeholder)
        if placeholder and self.set_placeholder and is_widget_with_placeholder(widget):
            # TODO: Should this be stripped and/or escaped?
            widget.attrs["placeholder"] = placeholder

    def add_help_attrs(self, widget=None):
        if widget is None:
            widget = self.widget
        if not isinstance(widget, CheckboxInput):
            widget.attrs["title"] = widget.attrs.get("title", escape(strip_tags(self.field_help)))

    def add_widget_attrs(self):
        if self.is_multi_widget:
            widgets = self.widget.widgets
        else:
            widgets = [self.widget]
        for widget in widgets:
            self.add_class_attrs(widget)
            self.add_placeholder_attrs(widget)
            self.add_help_attrs(widget)

    def radio_list_to_class(self, html, klass):
        classes = add_css_class(klass, self.get_size_class())
        mapping = [
            ("<ul", '<div class="{klass}"'.format(klass=classes)),
            ("</ul>", "</div>"),
            ("<li>", ""),
            ("</li>", ""),
        ]
        for k, v in mapping:
            html = html.replace(k, v)
        return html

    def list_to_class(self, html, klass):
        classes = add_css_class(klass, self.get_size_class())
        mapping = [
            ("<ul", "<div"),
            ("</ul>", "</div>"),
            ("<li", '<div class="{klass}"'.format(klass=classes)),
            ("</li>", "</div>"),
        ]
        for k, v in mapping:
            html = html.replace(k, v)
        return html

    def add_checkbox_label(self, html):
        return html + render_label(
            content=self.field.label,
            label_for=self.field.id_for_label,
            label_title=escape(strip_tags(self.field_help)),
            label_class="form-check-label",
        )

    def fix_date_select_input(self, html):
        div1 = '<div class="col-4">'
        div2 = "</div>"
        html = html.replace("<select", div1 + "<select")
        html = html.replace("</select>", "</select>" + div2)
        return '<div class="row bootstrap4-multi-input">' + html + "</div>"

    def fix_clearable_file_input(self, html):
        """
        Fix a clearable file input
        TODO: This needs improvement

        Currently Django returns
        Currently:
        <a href="dummy.txt">dummy.txt</a>
        <input id="file4-clear_id" name="file4-clear" type="checkbox" />
        <label for="file4-clear_id">Clear</label><br />
        Change: <input id="id_file4" name="file4" type="file" />
        <span class=help-block></span>
        </div>

        """
        # TODO This needs improvement
        return '<div class="row bootstrap4-multi-input"><div class="col-12">{html}</div></div>'.format(
            html=html
        )

    def post_widget_render(self, html):
        if isinstance(self.widget, RadioSelect):
            html = self.radio_list_to_class(html, "radio radio-success")
        elif isinstance(self.widget, CheckboxSelectMultiple):
            html = self.list_to_class(html, "checkbox")
        elif isinstance(self.widget, SelectDateWidget):
            html = self.fix_date_select_input(html)
        elif isinstance(self.widget, ClearableFileInput):
            html = self.fix_clearable_file_input(html)
        elif isinstance(self.widget, CheckboxInput):
            html = self.add_checkbox_label(html)
        return html

    def wrap_widget(self, html):
        if isinstance(self.widget, CheckboxInput):
            # Wrap checkboxes
            # Note checkboxes do not get size classes, see #318
            html = '<div class="form-check">{content}</div>'.format(content=html)
        return html

    def make_input_group_addon(self, inner_class, outer_class, content):
        if not content:
            return ""

        content = (
            '<span class="{input_class}">{addon}</span>'.format(
                input_class=inner_class, addon=content
            )
            if inner_class
            else content
        )

        return '<div class="{addon_class}">{addon}</div>'.format(
            addon_class=outer_class, addon=content
        )

    def make_input_group(self, html):
        allowed_widget_types = (
            TextInput,
            PasswordInput,
            DateInput,
            NumberInput,
            Select,
            EmailInput,
        )
        if (self.addon_before or self.addon_after) and isinstance(
            self.widget, allowed_widget_types
        ):
            html = '<div class="input-group">{before}{html}{after}</div>'.format(
                before=self.make_input_group_addon(
                    self.addon_before_class, "input-group-prepend", self.addon_before
                ),
                after=self.make_input_group_addon(
                    self.addon_after_class, "input-group-append", self.addon_after
                ),
                html=html,
            )
        return html

    def append_help_and_error(self, html):
        field_help = self.field_help or None
        field_errors = self.field_errors
        if field_help or field_errors:
            help_html = render_template_file(
                "bootstrap4/field_help_text_and_errors.html",
                context={
                    "field": self.field,
                    "field_help": field_help,
                    "field_errors": field_errors,
                    "layout": self.layout,
                    "show_help": self.show_help,
                },
            )
            html += help_html
        return html

    def append_to_field(self, html):
        if isinstance(self.widget, CheckboxInput):
            return html
        return self.append_help_and_error(html)

    def append_to_checkbox_field(self, html):
        if not isinstance(self.widget, CheckboxInput):
            return html
        return self.append_help_and_error(html)

    def get_field_class(self):
        field_class = self.field_class
        if not field_class and self.layout == "horizontal":
            field_class = self.horizontal_field_class
        return field_class

    def wrap_field(self, html):
        field_class = self.get_field_class()
        if field_class:
            html = '<div class="{klass}">{html}</div>'.format(klass=field_class, html=html)
        return html

    def get_label_class(self):
        label_class = self.label_class
        if not label_class and self.layout == "horizontal":
            label_class = self.horizontal_label_class
            label_class = add_css_class(label_class, "col-form-label")
        label_class = text_value(label_class)
        if not self.show_label:
            label_class = add_css_class(label_class, "sr-only")
        return label_class

    def get_label(self):
        if isinstance(self.widget, CheckboxInput):
            label = None
        else:
            label = self.field.label
        if self.layout == "horizontal" and not label:
            return mark_safe("&#160;")
        return label

    def add_label(self, html):
        label = self.get_label()
        if label:
            html = (
                render_label(
                    label, label_for=self.field.id_for_label, label_class=self.get_label_class()
                )
                + html
            )
        return html

    def get_form_group_class(self):
        form_group_class = self.form_group_class
        if self.field.errors:
            if self.error_css_class:
                form_group_class = add_css_class(form_group_class, self.error_css_class)
        else:
            if self.field.form.is_bound:
                form_group_class = add_css_class(form_group_class, self.success_css_class)
        if self.field.field.required and self.required_css_class:
            form_group_class = add_css_class(form_group_class, self.required_css_class)
        if self.layout == "horizontal":
            form_group_class = add_css_class(form_group_class, "row")
        return form_group_class

    def wrap_label_and_field(self, html):
        return render_form_group(html, self.get_form_group_class())

    def _render(self):
        # See if we're not excluded
        if self.field.name in self.exclude.replace(" ", "").split(","):
            return ""
        # Hidden input requires no special treatment
        if self.field.is_hidden:
            return text_value(self.field)
        # Render the widget
        self.add_widget_attrs()
        html = self.field.as_widget(attrs=self.widget.attrs)
        self.restore_widget_attrs()
        # Start post render
        html = self.post_widget_render(html)
        html = self.append_to_checkbox_field(html)
        html = self.wrap_widget(html)
        html = self.make_input_group(html)
        html = self.append_to_field(html)
        html = self.wrap_field(html)
        html = self.add_label(html)
        html = self.wrap_label_and_field(html)
        return html


class InlineFieldRenderer(FieldRenderer):
    """
    Inline field renderer
    """

    def add_error_attrs(self):
        field_title = self.widget.attrs.get("title", "")
        field_title += " " + " ".join([strip_tags(e) for e in self.field_errors])
        self.widget.attrs["title"] = field_title.strip()

    def add_widget_attrs(self):
        super(InlineFieldRenderer, self).add_widget_attrs()
        self.add_error_attrs()

    def append_to_field(self, html):
        return html

    def get_field_class(self):
        return self.field_class

    def get_label_class(self):
        return add_css_class(self.label_class, "sr-only")
