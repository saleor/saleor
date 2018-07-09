import saleor.discount.models as models
from modeltranslation.translator import TranslationOptions, register


@register(models.Sale)
class SaleTranslationOptions(TranslationOptions):
    fields = ('name',)
