from django.forms import Select


class DatalistTextWidget(Select):
    input_type = "text"

    def get_context(self, *args):
        context = super().get_context(*args)
        context["widget"]["type"] = self.input_type
        return context

    def format_value(self, value):
        value = super().format_value(value)
        return value[0]
