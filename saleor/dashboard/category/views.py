from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...product.models import Category


def category_list(request):
    categories = Category.objects.all()
    ctx = {'categories': categories}
    return TemplateResponse(request, 'dashboard/category/list.html', ctx)


def category_details(request, pk=None):
    if pk:
        category = get_object_or_404(Category.objects.all(), pk=pk)
        title = category.name
    else:
        category = Category()
        title = _('Add new category')
    ctx = {'category': category, 'title': title}
    return TemplateResponse(request, 'dashboard/category/detail.html', ctx)
