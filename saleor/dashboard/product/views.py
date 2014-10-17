from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView

from ...product.models import Product
from ..views import StaffMemberOnlyMixin, staff_member_required
from .forms import (ProductImageFormSet, ProductCategoryForm, get_product_form,
                    get_variant_formset)


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
    form = ProductCategoryForm(request.POST or None)
    if form.is_valid():
        category = form.cleaned_data['category']
        return redirect('dashboard:product-add', category=category)
    ctx = {'products': products, 'form': form, 'paginator': paginator}
    return TemplateResponse(request, 'dashboard/product/list.html', ctx)


@staff_member_required
def product_details(request, pk=None, category=None):
    product = get_object_or_404(
        Product.objects.select_subclasses(), pk=pk) if pk else None
    form_cls = get_product_form(product, category)
    variant_formset_cls = get_variant_formset(product, category)
    form = form_cls(request.POST or None, instance=product)
    variant_formset = variant_formset_cls(instance=product)
    image_formset = ProductImageFormSet(instance=product)
    err_msg = _('Your submitted data was not valid - please correct the errors'
                ' below')
    if form.is_valid():
        product = form.save()
        variant_formset = variant_formset_cls(request.POST,
                                              instance=product)
        image_formset = ProductImageFormSet(request.POST, request.FILES,
                                            instance=product)
        if variant_formset.is_valid() and image_formset.is_valid():
            variant_formset.save()
            image_formset.save()
            if pk:
                msg = _('Product %s updated' % product)
            else:
                msg = _('Product %s added' % product)
            messages.success(request, msg)
            return redirect('dashboard:products')
        else:
            messages.error(request, err_msg)
    else:
        if form.errors:
            messages.error(request, err_msg)
    title = product.name if product else _('Add new product')
    ctx = {'title': title, 'product': product, 'form': form,
           'variant_formset': variant_formset, 'image_formset': image_formset}
    return TemplateResponse(request, 'dashboard/product/product_form.html', ctx)


class ProductDeleteView(StaffMemberOnlyMixin, DeleteView):
    model = Product
    template_name = 'dashboard/product/product_confirm_delete.html'
    success_url = reverse_lazy('dashboard:products')

    def post(self, request, *args, **kwargs):
        result = self.delete(request, *args, **kwargs)
        messages.success(request, _('Deleted product %s' % self.object))
        return result
