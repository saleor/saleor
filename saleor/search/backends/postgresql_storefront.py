from ...product.models import Product
from django.db.models import Q
from django.contrib.postgres.search import TrigramSimilarity


def search(phrase):
    '''Storefront full text product search

    Fuzzy storefront search that is resistant to small typing errors made
    by user. Name is matched using trigram similarity, description uses
    standard postgres full text search.

    Args:
        phrase (str): searched phrase

    '''
    name_sim = TrigramSimilarity('name', phrase)
    published = Q(is_published=True)
    ft_in_description = Q(description__search=phrase)
    name_similar = Q(name_sim__gt=0.2)
    return Product.objects.annotate(name_sim=name_sim).filter(
        (ft_in_description | name_similar) & published)
