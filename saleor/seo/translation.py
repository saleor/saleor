from modeltranslation.translator import register, TranslationOptions
import saleor.seo.models as models

@register(models.SeoModel)
class SeoModelTranslationOptions(TranslationOptions):
    fields = ('seo_title', 'seo_description',)
