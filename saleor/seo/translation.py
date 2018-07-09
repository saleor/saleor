import saleor.seo.models as models
from modeltranslation.translator import TranslationOptions, register


@register(models.SeoModel)
class SeoModelTranslationOptions(TranslationOptions):
    fields = ('seo_title', 'seo_description',)
