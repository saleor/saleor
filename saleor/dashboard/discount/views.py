from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from ...product.models import FixedProductDiscount
from . import forms


@staff_member_required
def discount_list(request):
    discounts = FixedProductDiscount.objects.prefetch_related('products')
    ctx = {'discounts': discounts}
    return TemplateResponse(request, 'dashboard/discount/list.html',
                            ctx)


@staff_member_required
def discount_edit(request, pk=None):
    if pk:
        instance = get_object_or_404(FixedProductDiscount, pk=pk)
    else:
        instance = FixedProductDiscount()
    form = forms.FixedProductDiscountForm(
        request.POST or None, instance=instance)
    if form.is_valid():
        instance = form.save()
        msg = _('Updated discount') if pk else _('Added discount')
        messages.success(request, msg)
        return redirect('dashboard:discount-update', pk=instance.pk)
    ctx = {'discount': instance, 'form': form}
    return TemplateResponse(request, 'dashboard/discount/form.html',
                            ctx)


@staff_member_required
def discount_delete(request, pk):
    instance = get_object_or_404(FixedProductDiscount, pk=pk)
    if request.method == 'POST':
        instance.delete()
        messages.success(
            request, _('Deleted discount %s') % (instance.name,))
        return redirect('dashboard:discount-list')
    ctx = {'discount': instance}
    return TemplateResponse(
        request, 'dashboard/product/discount/modal_confirm_delete.html', ctx)
