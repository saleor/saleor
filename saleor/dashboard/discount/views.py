from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from ...discount.models import Sale
from . import forms


@staff_member_required
def sale_list(request):
    sales = Sale.objects.prefetch_related('products')
    ctx = {'sales': sales}
    return TemplateResponse(request, 'dashboard/discount/sale_list.html', ctx)


@staff_member_required
def sale_edit(request, pk=None):
    if pk:
        instance = get_object_or_404(Sale, pk=pk)
    else:
        instance = Sale()
    form = forms.SaleForm(
        request.POST or None, instance=instance)
    if form.is_valid():
        instance = form.save()
        msg = _('Updated sale') if pk else _('Added sale')
        messages.success(request, msg)
        return redirect('dashboard:sale-update', pk=instance.pk)
    ctx = {'sale': instance, 'form': form}
    return TemplateResponse(request, 'dashboard/discount/sale_form.html', ctx)


@staff_member_required
def sale_delete(request, pk):
    instance = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        instance.delete()
        messages.success(
            request, _('Deleted sale %s') % (instance.name,))
        return redirect('dashboard:sale-list')
    ctx = {'sale': instance}
    return TemplateResponse(
        request, 'dashboard/discount/sale_modal_confirm_delete.html', ctx)
