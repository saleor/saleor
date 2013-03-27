import re
from django.forms.widgets import TextInput


class CreditCardNumberWidget(TextInput):
    def render(self, name, value, attrs):
        if value:
            value = re.sub('[\s-]', '', value)
            value = ' '.join([value[i:i+4] for i in range(0, len(value), 4)])
        return super(CreditCardNumberWidget, self).render(name, value, attrs)
