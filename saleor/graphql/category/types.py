from ...product.models import Category


def resolve_categories(parent, info):
    if parent == -1:
        parent = None
    categories = Category.objects.filter(parent=parent).distinct()
    return categories
