from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView

from ...product.models import Product
from ..views import StaffMemberOnlyMixin, staff_member_required
from .forms import (ProductImageFormSet, ProductClassForm, get_product_form,
                    get_product_cls_by_name, get_variant_formset)


@staff_member_required
def product_list(request):
    products = Product.objects.prefetch_related('images').select_subclasses()
    paginator = Paginator(products, 30)
    try:
        products = paginator.page(request.GET.get('page'))
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    form = ProductClassForm(request.POST or None)
    if form.is_valid():
        cls_name = form.cleaned_data['cls_name']
        return redirect('dashboard:product-add', cls_name=cls_name)
    ctx = {'products': products, 'form': form, 'paginator': paginator}
    return TemplateResponse(request, 'dashboard/product/list.html', ctx)


@staff_member_required
def product_details(request, pk=None, cls_name=None):
    if pk:
        product = get_object_or_404(Product.objects.select_subclasses(), pk=pk)
    else:
        product = get_product_cls_by_name(cls_name)()

    form_cls = get_product_form(product)
    variant_formset_cls = get_variant_formset(product)

    form = form_cls(request.POST or None, instance=product)
    variant_formset = variant_formset_cls(
        request.POST or None, instance=product)
    image_formset = ProductImageFormSet(
        request.POST or None, request.FILES or None, instance=product)

    forms = {'form': form, 'variant_formset': variant_formset,
             'image_formset': image_formset}

    if all([f.is_valid() for f in forms.values()]):
        product = form.save()
        variant_formset.save()
        image_formset.save()
        if pk:
            msg = _('Product %s updated' % product)
        else:
            msg = _('Product %s added' % product)
        messages.success(request, msg)
        return redirect('dashboard:products')
    else:
        if any([f.errors for f in forms.values()]):
            messages.error(request, _('Your submitted data was not valid - '
                           'please correct the errors below'))

    title = product.name if product else _('Add new product')
    ctx = {'title': title, 'product': product}
    ctx.update(forms)
    return TemplateResponse(request, 'dashboard/product/product_form.html', ctx)


class ProductDeleteView(StaffMemberOnlyMixin, DeleteView):
    model = Product
    template_name = 'dashboard/product/product_confirm_delete.html'
    success_url = reverse_lazy('dashboard:products')

    def post(self, request, *args, **kwargs):
        result = self.delete(request, *args, **kwargs)
        messages.success(request, _('Deleted product %s' % self.object))
        return result
