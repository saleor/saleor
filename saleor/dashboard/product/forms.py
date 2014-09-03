from django.forms.models import inlineformset_factory
from ...product.models import ProductImage, Product


ProductImageFormSet = inlineformset_factory(Product, ProductImage, extra=2)
