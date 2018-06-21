from modeltranslation.translator import register, TranslationOptions
import saleor.discount.models as models

@register(models.Sale)
class SaleTranslationOptions(TranslationOptions):
    fields = ('name',)
