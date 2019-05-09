from django.forms.widgets import RadioSelect


class RadioSelectButtonGroup(RadioSelect):
    """
    This widget renders a Bootstrap 4 set of buttons horizontally
    instead of typical radio buttons. Much more mobile friendly.
    """

    template_name = "bootstrap4/widgets/radio_select_button_group.html"
