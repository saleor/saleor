from bootstrap3.renderers import FormRenderer as BaseFormRenderer


class FormRenderer(BaseFormRenderer):

    def render_errors(self, type='non_fields'):
        return super().render_errors(type)
