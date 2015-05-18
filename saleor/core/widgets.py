from django.utils.html import escape
from django.utils.safestring import mark_safe
from django_prices.widgets import PriceInput as BasePriceInput


class PriceInput(BasePriceInput):
    TEMPLATE = '''<div class="input-group">
    %(widget)s
    <div class="input-group-addon">%(currency)s</div>
</div>'''

    def render(self, name, value, attrs=None):
        widget = super(BasePriceInput, self).render(name, value, attrs)
        result = self.TEMPLATE % {'widget': widget,
                                  'currency': escape(self.currency)}
        return mark_safe(result)
