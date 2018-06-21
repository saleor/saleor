from modeltranslation.translator import register, TranslationOptions
import saleor.menu.models as models

@register(models.MenuItem)
class MenuItemTranslationOptions(TranslationOptions):
    fields = ('name',)
