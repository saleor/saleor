from modeltranslation.translator import register, TranslationOptions
import saleor.page.models as models

@register(models.Page)
class SeoModelTranslationOptions(TranslationOptions):
    fields = ('title', 'content', 'slug',)
