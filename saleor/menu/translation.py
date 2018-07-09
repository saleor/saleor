import saleor.menu.models as models
from modeltranslation.translator import TranslationOptions, register


@register(models.MenuItem)
class MenuItemTranslationOptions(TranslationOptions):
    fields = ('name',)
