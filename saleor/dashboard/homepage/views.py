from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse

from ...homepage.models import HomePageItem
from ..views import staff_member_required
from .forms import BlockItemForm


@staff_member_required
@permission_required('homepage.view_blocks_config')
def homepage_block_list(request):
    blocks = HomePageItem.objects.all()
    ctx = {'blocks': blocks}
    return TemplateResponse(
        request, 'dashboard/homepage-blocks/list.html', ctx)


def _handle_homepage_block_form(request, instance=None):
    form = BlockItemForm(
        request.POST or None, request.FILES or None, instance=instance)
    status = 200

    if form.is_valid():
        form.save()
        return redirect('dashboard:homepage-blocks-list')
    elif form.errors:
        status = 400

    ctx = {'form': form, 'page_block': instance}
    return TemplateResponse(
        request, 'dashboard/homepage-blocks/form.html', ctx, status=status)


@staff_member_required
@permission_required('homepage.edit_blocks_config')
def homepage_block_create(request):
    return _handle_homepage_block_form(request)


@staff_member_required
@permission_required('homepage.edit_blocks_config')
def homepage_block_edit(request, pk):
    block_instance = get_object_or_404(HomePageItem, pk=pk)
    return _handle_homepage_block_form(request, block_instance)


@staff_member_required
@permission_required('homepage.edit_blocks_config')
def homepage_block_delete(request, pk):
    block_instance = get_object_or_404(HomePageItem, pk=pk)
    if request.method == 'POST':
        block_instance.delete()
        return redirect('dashboard:homepage-blocks-list')

    ctx = {'page_block': block_instance}
    return TemplateResponse(
        request, 'dashboard/homepage-blocks/modals/delete.html', ctx)
