from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _

from ...product.models import Category
from ..views import staff_member_required
from .forms import CategoryForm


@staff_member_required
def category_list(request, root_pk=None):
    root = None
    path = None
    categories = Category.tree.root_nodes()
    if root_pk:
        root = get_object_or_404(Category, pk=root_pk)
        path = root.get_ancestors(include_self=True) if root else []
        categories = root.get_children()
    ctx = {'categories': categories, 'path': path, 'root': root}
    return TemplateResponse(request, 'dashboard/category/list.html', ctx)


@staff_member_required
def category_create(request, root_pk=None):
    category = Category()
    form = CategoryForm(request.POST or None, parent_pk=root_pk)
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
def category_edit(request, root_pk=None):
    category = get_object_or_404(Category, pk=root_pk)
    form = CategoryForm(request.POST or None, instance=category,
                        parent_pk=category.parent_id)
    status = 200
    if form.is_valid():
        category = form.save()
        messages.success(request, _('Added category %s') % category)
        if root_pk:
            return redirect('dashboard:category-list', root_pk=root_pk)
        else:
            return redirect('dashboard:category-list')
    elif form.errors:
        status = 400
    ctx = {'category': category, 'form': form, 'status': status}
    template = 'dashboard/category/modal_edit.html'
    return TemplateResponse(request, template, ctx, status=status)


@staff_member_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, _('Deleted category %s') % category)
        root_pk = None
        if category.parent:
            root_pk = category.parent.pk
        if root_pk:
            if request.is_ajax():
                response = {'redirectUrl': reverse(
                    'dashboard:category-list', kwargs={'root_pk': root_pk})}
                return JsonResponse(response)
            return redirect('dashboard:category-list', root_pk=root_pk)
        else:
            if request.is_ajax():
                response = {'redirectUrl': reverse('dashboard:category-list')}
                return JsonResponse(response)
            return redirect('dashboard:category-list')
    ctx = {'category': category,
           'descendants': list(category.get_descendants()),
           'products_count': len(category.products.all())}
    return TemplateResponse(request,
                            'dashboard/category/modal_delete.html',
                            ctx)
