from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...product.models import Category
from ..views import staff_member_required
from .forms import CategoryForm


@staff_member_required
def category_root_nodes_list(request):
    categories = Category.tree.root_nodes()
    ctx = {'categories': categories, 'path': [], 'root': None, 'form': None}
    return TemplateResponse(request, 'dashboard/category/list.html', ctx)


@staff_member_required
def category_children_nodes_list(request, root_pk):
    root = get_object_or_404(Category, pk=root_pk)
    category = get_object_or_404(Category,
                                 pk=root.parent.pk) if root.parent else None
    form = CategoryForm(request.POST or None, instance=root,
                        initial={'parent': category})
    if form.is_valid():
        category = form.save()
        messages.success(request, _('Updated category %s') % category)
        if root:
            return redirect('dashboard:category-children-list', root_pk=root.pk)
        else:
            return redirect('dashboard:category-root-list')
    path = root.get_ancestors(include_self=True) if root else []
    categories = root.get_children()
    ctx = {'categories': categories, 'path': path, 'root': root, 'form': form}
    return TemplateResponse(request, 'dashboard/category/list.html', ctx)


@staff_member_required
def category_create(request, root_pk=None):
    category = Category()
    form = CategoryForm(request.POST or None, initial={'parent': root_pk})
    if form.is_valid():
        category = form.save()
        messages.success(request, _('Added category %s') % category)
        if root_pk:
            return redirect('dashboard:category-children-list', root_pk=root_pk)
        else:
            return redirect('dashboard:category-root-list')
    ctx = {'category': category, 'form': form}
    return TemplateResponse(request, 'dashboard/category/detail.html', ctx)


@staff_member_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, _('Deleted category %s') % category)
        if category.parent:
            return redirect('dashboard:category-children-list', root_pk=category.parent.pk)
        else:
            return redirect('dashboard:category-root-list')
    ctx = {'category': category,
           'descendants': list(category.get_descendants()),
           'products_count': len(category.products.all())}
    return TemplateResponse(request,
                            'dashboard/category/category_confirm_delete.html',
                            ctx)