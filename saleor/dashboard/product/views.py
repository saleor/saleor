from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.views.generic import ListView, DeleteView
from django.views.generic.edit import FormMixin
from django.utils.translation import ugettext_lazy as _
from ..views import StaffMemberOnlyMixin
from ...product.models import Product
from .forms import (ProductImageFormSet, ProductCategoryForm, get_product_form,
                    get_variant_formset)


class ProductListView(StaffMemberOnlyMixin, ListView, FormMixin):
    model = Product
    paginate_by = 30
    template_name = 'dashboard/product/list.html'
    context_object_name = 'products'
    form_class = ProductCategoryForm

    def get_queryset(self):
        qs = super(ProductListView, self).get_queryset()
        qs = qs.prefetch_related('images').select_related('brand')
        qs = qs.select_subclasses()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super(ProductListView, self).get_context_data(**kwargs)
        ctx['form'] = self.form_class()
        return ctx

    def post(self, request, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            return HttpResponseRedirect(reverse(
                'dashboard:product-add',
                kwargs={'category': form.cleaned_data['category']}))
        return self.get(request, **kwargs)


def product_details(request, pk=None, category=None):
    product = Product.objects.select_subclasses().get(pk=pk) if pk else None
    form_cls = get_product_form(product, category)
    variant_formset_cls = get_variant_formset(product, category)
    form = form_cls(request.POST or None, instance=product)
    if request.method == 'POST':
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
                    messages.success(request, _('Product %s updated' % product))
                    return redirect('dashboard:product-update', pk=product.pk)
                else:
                    messages.success(request, _('Product %s added' % product))
                    return redirect('dashboard:products')
            else:
                error = True
        else:
            error = True
        if error:
            messages.error(request, _('Your submitted data was not valid'
                                      ' - please correct the errors below'))
    else:
        variant_formset = variant_formset_cls(instance=product)
        image_formset = ProductImageFormSet(instance=product)
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
