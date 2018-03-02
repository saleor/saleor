from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...core.utils import get_paginator_items
from ...menu.models import Menu
from ..views import staff_member_required
from .filters import MenuItemFilter, MenuFilter
from .forms import MenuForm


@staff_member_required
@permission_required('menu.view_menu')
def menu_list(request):
    menus = Menu.objects.all()
    menu_filter = MenuFilter(request.GET, queryset=menus)
    menus = get_paginator_items(
        menu_filter.qs, settings.DASHBOARD_PAGINATE_BY,
        request.GET.get('page'))
    ctx = {'menus': menus, 'filter_set': menu_filter,
           'is_empty': not menu_filter.queryset.exists()}
    return TemplateResponse(request, 'dashboard/menu/list.html', ctx)


@staff_member_required
@permission_required('menu.edit_menu')
def menu_create(request):
    menu = Menu()
    form = MenuForm(request.POST or None, instance=menu)
    if form.is_valid():
        menu = form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Add menu %s') % (menu,)
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
        return redirect('dashboard:menu-detail', pk=menu.pk)
    ctx = {'form': form, 'menu': menu}
    template = 'dashboard/menu/form.html'
    return TemplateResponse(request, template, ctx)


@staff_member_required
@permission_required('menu.view_menu')
def menu_detail(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    menu_items = menu.items.all()
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
    ctx = {'menu': menu, 'menu_items_count': menu.items.count()}
    return TemplateResponse(
        request, 'dashboard/menu/modal/confirm_delete.html', ctx)
