from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...product.models import Category
from ..views import staff_member_required
from .forms import CategoryForm


@staff_member_required
def category_list(request, root=None):
    ctx = {}
    categories = Category.objects.all()
    if root:
        current_node = get_object_or_404(Category, pk=root)
        categories = current_node.get_descendants()
        ctx['current_node'] = current_node
        ctx['category_breadcrumbs'] = current_node.get_ancestors(include_self=True)
    min_level = categories[0].get_level() if categories else 0
    max_level = min_level + 1
    categories = categories.filter(level__gte=min_level, level__lte=max_level)
    ctx['categories'] = categories
    ctx['min_level'] = min_level
    return TemplateResponse(request, 'dashboard/category/list.html', ctx)


@staff_member_required
def category_details(request, pk=None, parent_pk=None):
    if pk:
        category = get_object_or_404(Category.objects.all(), pk=pk)
        title = category.name
    else:
        category = Category()
        title = _('Add new category')
    form = CategoryForm(request.POST or None, instance=category,
                        initial={'parent': parent_pk})
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


@staff_member_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, _('Deleted category %s') % category)
        return redirect('dashboard:categories')
    ctx = {'category': category,
           'descendants': list(category.get_descendants()),
           'products_count': len(category.products.all())}
    return TemplateResponse(request,
                            'dashboard/category/category_confirm_delete.html',
                            ctx)