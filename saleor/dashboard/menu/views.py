from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import pgettext_lazy

from ...core.utils import get_paginator_items
from ...menu.models import Menu, MenuItem
from ...page.models import Page
from ...product.models import Category, Collection
from ..views import staff_member_required
from .filters import MenuFilter, MenuItemFilter
from .forms import AssignMenuForm, MenuForm, MenuItemForm, ReorderMenuItemsForm


@staff_member_required
@permission_required('menu.view_menu')
def menu_list(request):
    menus = Menu.objects.all()
    menu_filter = MenuFilter(request.GET, queryset=menus)
    menus = get_paginator_items(
        menu_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    site_settings = request.site.settings

    data = (
        request.POST
        if request.user.has_perm('menu.edit_menu') and request.POST
        else None)
    assign_menu_form = AssignMenuForm(
        data, instance=site_settings, user=request.user)
    if request.method == 'POST' and assign_menu_form.is_valid():
        assign_menu_form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated storefront menus')
        messages.success(request, msg)
        return redirect('dashboard:menu-list')
    ctx = {
        'menus': menus, 'filter_set': menu_filter,
        'is_empty': not menu_filter.queryset.exists(),
        'assign_menu_form': assign_menu_form}
    return TemplateResponse(request, 'dashboard/menu/list.html', ctx)


@staff_member_required
@permission_required('menu.edit_menu')
def menu_create(request):
    menu = Menu()
    form = MenuForm(request.POST or None, instance=menu)
    if form.is_valid():
        menu = form.save()
        msg = pgettext_lazy('Dashboard message', 'Added menu %s') % (menu,)
        messages.success(request, msg)
        return redirect('dashboard:menu-list')
    ctx = {'form': form, 'menu': menu}
    return TemplateResponse(request, 'dashboard/menu/form.html', ctx)


@staff_member_required
@permission_required('menu.edit_menu')
def menu_edit(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    form = MenuForm(request.POST or None, instance=menu)
    if form.is_valid():
        menu = form.save()
        msg = pgettext_lazy('Dashboard message', 'Updated menu %s') % (menu,)
        messages.success(request, msg)
        return redirect('dashboard:menu-details', pk=menu.pk)
    ctx = {'form': form, 'menu': menu}
    template = 'dashboard/menu/form.html'
    return TemplateResponse(request, template, ctx)


@staff_member_required
@permission_required('menu.view_menu')
def menu_details(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    menu_items = menu.items.filter(parent=None).prefetch_related(
        'category', 'collection', 'page')
    menu_item_filter = MenuItemFilter(request.GET, queryset=menu_items)
    menu_items = get_paginator_items(
        menu_item_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'menu': menu, 'menu_items': menu_items, 'filter_set': menu_item_filter,
        'is_empty': not menu_item_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/menu/detail.html', ctx)


@staff_member_required
@permission_required('menu.edit_menu')
def menu_delete(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    if request.method == 'POST':
        menu.delete()
        msg = pgettext_lazy('Dashboard message', 'Removed menu %s') % (menu,)
        messages.success(request, msg)
        return redirect('dashboard:menu-list')
    ctx = {
        'menu': menu, 'descendants': list(menu.items.all())}
    return TemplateResponse(
        request, 'dashboard/menu/modal/confirm_delete.html', ctx)


@staff_member_required
@permission_required('menu.edit_menu')
def menu_item_create(request, menu_pk, root_pk=None):
    menu = get_object_or_404(Menu, pk=menu_pk)
    path = None
    if root_pk:
        root = get_object_or_404(MenuItem, pk=root_pk)
        path = root.get_ancestors(include_self=True)
        menu_item = MenuItem(menu=menu, parent=root)
    else:
        menu_item = MenuItem(menu=menu)
    form = MenuItemForm(request.POST or None, instance=menu_item)
    if form.is_valid():
        menu_item = form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added menu item %s') % (menu_item,)
        messages.success(request, msg)
        if root_pk:
            return redirect(
                'dashboard:menu-item-details',
                menu_pk=menu.pk, item_pk=root_pk)
        return redirect('dashboard:menu-details', pk=menu.pk)
    ctx = {
        'form': form, 'menu': menu, 'menu_item': menu_item, 'path': path}
    return TemplateResponse(request, 'dashboard/menu/item/form.html', ctx)


@staff_member_required
@permission_required('menu.edit_menu')
def menu_item_edit(request, menu_pk, item_pk):
    menu = get_object_or_404(Menu, pk=menu_pk)
    menu_item = get_object_or_404(menu.items.all(), pk=item_pk)
    path = menu_item.get_ancestors(include_self=True)
    form = MenuItemForm(request.POST or None, instance=menu_item)
    if form.is_valid():
        menu_item = form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Saved menu item %s') % (menu_item,)
        messages.success(request, msg)
        return redirect(
            'dashboard:menu-item-details', menu_pk=menu.pk, item_pk=item_pk)
    ctx = {
        'form': form, 'menu': menu, 'menu_item': menu_item, 'path': path}
    return TemplateResponse(request, 'dashboard/menu/item/form.html', ctx)


@staff_member_required
@permission_required('menu.edit_menu')
def menu_item_delete(request, menu_pk, item_pk):
    menu = get_object_or_404(Menu, pk=menu_pk)
    menu_item = get_object_or_404(menu.items.all(), pk=item_pk)
    if request.method == 'POST':
        menu_item.delete()
        msg = pgettext_lazy(
            'Dashboard message', 'Removed menu item %s') % (menu_item,)
        messages.success(request, msg)
        root_pk = menu_item.parent.pk if menu_item.parent else None
        if root_pk:
            redirect_url = reverse(
                'dashboard:menu-item-details', kwargs={
                    'menu_pk': menu_item.menu.pk, 'item_pk': root_pk})
        else:
            redirect_url = reverse(
                'dashboard:menu-details', kwargs={'pk': menu.pk})
        return (
            JsonResponse({'redirectUrl': redirect_url}) if request.is_ajax()
            else redirect(redirect_url))
    ctx = {
        'menu_item': menu_item,
        'descendants': list(menu_item.get_descendants())}
    return TemplateResponse(
        request, 'dashboard/menu/item/modal/confirm_delete.html', ctx)


@staff_member_required
@permission_required('menu.view_menu')
def menu_item_details(request, menu_pk, item_pk):
    menu = get_object_or_404(Menu, pk=menu_pk)
    menu_item = get_object_or_404(menu.items.all(), pk=item_pk)
    path = menu_item.get_ancestors(include_self=True)
    menu_items = menu_item.get_children().order_by('sort_order')
    menu_item_filter = MenuItemFilter(request.GET, queryset=menu_items)
    menu_items = get_paginator_items(
        menu_item_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {
        'menu': menu, 'menu_item': menu_item, 'menu_items': menu_items,
        'path': path, 'filter_set': menu_item_filter,
        'is_empty': not menu_item_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/menu/item/detail.html', ctx)


@staff_member_required
@permission_required('menu.edit_menu')
def ajax_reorder_menu_items(request, menu_pk, root_pk=None):
    menu = get_object_or_404(Menu, pk=menu_pk)
    if root_pk:
        root = get_object_or_404(MenuItem, pk=root_pk)
        form = ReorderMenuItemsForm(request.POST, instance=menu, parent=root)
    else:
        form = ReorderMenuItemsForm(request.POST, instance=menu)
    status = 200
    ctx = {}
    if form.is_valid():
        form.save()
    elif form.errors:
        status = 400
        ctx = {'error': form.errors}
    return JsonResponse(ctx, status=status)


@staff_member_required
@permission_required('menu.view_menu')
def ajax_menu_links(request):
    """Return available menu links filtered by request GET parameters.

    Response format is that of a Select2 JS widget.
    """
    def get_obj_repr(obj):
        obj_id = str(obj.pk) + '_' + obj.__class__.__name__
        return {'id': obj_id, 'text': str(obj)}

    def get_group_repr(model, label, filter_fields, query):
        queryset = model.objects.all()
        if search_query and search_query.lower() not in label.lower():
            kwargs = {
                '%s__icontains' % (field,): query
                for field in filter_fields}
            queryset = queryset.filter(Q(**kwargs))
        return {
            'text': label,
            'children': [get_obj_repr(obj) for obj in queryset]}

    search_query = request.GET.get('q', '')
    groups = [
        get_group_repr(
            Collection,
            pgettext_lazy('Link object type group description', 'Collection'),
            ('name',),
            search_query),
        get_group_repr(
            Category,
            pgettext_lazy('Link object type group description', 'Category'),
            ('name',),
            search_query),
        get_group_repr(
            Page,
            pgettext_lazy('Link object type group description', 'Page'),
            ('title',),
            search_query)
    ]

    groups = [group for group in groups if len(group.get('children')) > 0]
    return JsonResponse({'results': groups})
