import saleor.page.models as models
from modeltranslation.translator import TranslationOptions, register


@register(models.Page)
class SeoModelTranslationOptions(TranslationOptions):
    fields = ('title', 'content', 'slug',)
