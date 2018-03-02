from django.contrib.auth.decorators import permission_required
from django.template.response import TemplateResponse

from ..views import staff_member_required
from ...menu.models import Menu


@staff_member_required
@permission_required('menu.view_menus')
def menu_list(request):
    menus = Menu.objects.all()
    ctx = {'menus': menus}
    return TemplateResponse(request, 'dashboard/menu/list.html', ctx)
