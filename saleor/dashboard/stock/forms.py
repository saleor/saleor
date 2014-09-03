from django.forms.models import inlineformset_factory
from ...stock.models import StockRecord
from ...product.models import Product


BaseStockRecordFormSet = inlineformset_factory(Product, StockRecord, extra=1)


class StockRecordFormSet(BaseStockRecordFormSet):
    def __init__(self, *args, **kwargs):
        super(StockRecordFormSet, self).__init__(*args, **kwargs)
        # Require at least one Stock record
        self.forms[0].empty_permitted = False
