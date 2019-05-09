# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from bootstrap4.utils import render_tag, add_css_class

from .text import text_value


def render_alert(content, alert_type=None, dismissable=True):
    """
    Render a Bootstrap alert
    """
    button = ""
    if not alert_type:
        alert_type = "info"
    css_classes = ["alert", "alert-" + text_value(alert_type)]
    if dismissable:
        css_classes.append("alert-dismissable")
        button = (
            '<button type="button" class="close" '
            + 'data-dismiss="alert" aria-label="{}">&times;</button>'
        )
        button = button.format(_("close"))
    button_placeholder = "__BUTTON__"
    return mark_safe(
        render_tag(
            "div",
            attrs={"class": " ".join(css_classes), "role": "alert"},
            content=button_placeholder + text_value(content),
        ).replace(button_placeholder, button)
    )
