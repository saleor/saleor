from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...product.models import Category
from ..views import staff_member_required
from .forms import CategoryForm


@staff_member_required
def category_list(request, root_pk=None):
    root = None
    form = None
    if root_pk:
        root = get_object_or_404(Category, pk=root_pk)
        category = None
        if root.parent:
            category = get_object_or_404(Category, pk=root.parent.pk)
        categories = root.get_children()
        form = CategoryForm(request.POST or None,
                        instance=root,
                        initial={'parent': category})
        if form.is_valid():
            category = form.save()
            messages.success(request, _('Updated category %s') % category)
            if root:
                return redirect('dashboard:category-list', root_pk=root.pk)
            else:
                return redirect('dashboard:category-list')
    else:
        categories = Category.tree.root_nodes()
    path = root.get_ancestors(include_self=True) if root else []
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
            return redirect('dashboard:category-list', root_pk=root_pk)
        else:
            return redirect('dashboard:category-list')
    ctx = {'category': category, 'form': form}
    return TemplateResponse(request, 'dashboard/category/detail.html', ctx)


@staff_member_required
def category_edit(request, pk=None):
    category = get_object_or_404(Category, pk=pk)
    root = category.parent
    form = CategoryForm(request.POST or None,
                        instance=category,
                        initial={'parent': root})
    if form.is_valid():
        category = form.save()
        messages.success(request, _('Updated category %s') % category)
        if root:
            return redirect('dashboard:category-list', root_pk=root.pk)
        else:
            return redirect('dashboard:category-list')
    ctx = {'category': category, 'form': form}
    return TemplateResponse(request, 'dashboard/category/detail.html', ctx)


@staff_member_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, _('Deleted category %s') % category)
        if category.parent:
            return redirect('dashboard:category-list', root_pk=category.parent.pk)
        else:
            return redirect('dashboard:category-list')
    ctx = {'category': category,
           'descendants': list(category.get_descendants()),
           'products_count': len(category.products.all())}
    return TemplateResponse(request,
                            'dashboard/category/category_confirm_delete.html',
                            ctx)