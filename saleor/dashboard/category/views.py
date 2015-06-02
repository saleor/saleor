from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...product.models import Category
from .forms import CategoryForm


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
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        form.save()
        if pk:
            msg = _('Updated category %s') % category
        else:
            msg = _('Added category %s') % category
        messages.success(request, msg)
        return redirect('dashboard:categories')
    else:
        if form.errors:
            messages.error(request, _('Failed to save category'))
    ctx = {'category': category, 'form': form, 'title': title}
    return TemplateResponse(request, 'dashboard/category/detail.html', ctx)
