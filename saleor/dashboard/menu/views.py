from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import pgettext_lazy

from ...menu.models import Menu
from ..views import staff_member_required
from .forms import MenuForm


@staff_member_required
@permission_required('menu.view_menu')
def menu_list(request):
    menus = Menu.objects.all()
    ctx = {'menus': menus}
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
