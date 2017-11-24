from ...product.models import Product
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity


def search(phrase):
    name_sim = TrigramSimilarity('name', phrase)
    return Product.objects.annotate(name_sim=name_sim).filter(
        Q(description__search=phrase) | Q(name_sim__gt=0.1))
