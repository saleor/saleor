from modeltranslation.translator import register, TranslationOptions
import saleor.product.models as models

@register(models.Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description',)

@register(models.Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'slug',)

@register(models.ProductType)
class ProductTypeTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(models.ProductVariant)
class ProductVariantTranslationOptions(TranslationOptions):
    fields = ('name',)

@register(models.ProductAttribute)
class ProductAttributeTranslationOptions(TranslationOptions):
    fields = ('name', 'slug',)

@register(models.AttributeChoiceValue)
class AttributeChoiceValueTranslationOptions(TranslationOptions):
    fields = ('name', 'slug',)

@register(models.Collection)
class CollectionTranslationOptions(TranslationOptions):
    fields = ('name', 'slug',)
