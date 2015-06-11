from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView

from ...product.models import Product, ProductImage
from ..utils import paginate
from ..views import StaffMemberOnlyMixin, staff_member_required
from .forms import (ProductClassForm, get_product_form,
                    get_product_cls_by_name, get_variant_formset,
                    ProductImageForm, PRODUCT_CLASSES)


@staff_member_required
def product_list(request):
    products = Product.objects.prefetch_related('images').select_subclasses()
    form = ProductClassForm(request.POST or None)
    if form.is_valid():
        product_cls = form.cleaned_data['product_cls']
        return redirect('dashboard:product-add', product_cls=product_cls)
    products, paginator = paginate(products, 30, request.GET.get('page'))
    ctx = {'products': products, 'form': form, 'paginator': paginator}
    return TemplateResponse(request, 'dashboard/product/list.html', ctx)


@staff_member_required
def product_details(request, pk=None, product_cls=None):
    if pk:
        product = get_object_or_404(Product.objects.select_subclasses(), pk=pk)
        title = product.name
    else:
        product = get_product_cls_by_name(product_cls)()
        title = _('Add new %s') % product_cls
    images = product.images.all()
    form_cls = get_product_form(product)
    variant_formset_cls = get_variant_formset(product)
    form = form_cls(request.POST or None, instance=product)
    variant_formset = variant_formset_cls(
        request.POST or None, instance=product)
    forms = {'form': form, 'variant_formset': variant_formset}
    if all([f.is_valid() for f in forms.values()]):
        with transaction.atomic():
            product = form.save()
            variant_formset.save()
        if pk:
            msg = _('Updated product %s') % product
        else:
            msg = _('Added product %s') % product
        messages.success(request, msg)
        return redirect('dashboard:products')
    else:
        if any([f.errors for f in forms.values()]):
            messages.error(request, _('Your submitted data was not valid - '
                           'please correct the errors below'))
    ctx = {'title': title, 'product': product, 'images': images}
    ctx.update(forms)
    if pk:
        images_reorder_url = reverse_lazy('dashboard:product-images-reorder',
                                      kwargs={'product_pk': pk})
        ctx['images_reorder_url'] = images_reorder_url
    return TemplateResponse(request, 'dashboard/product/product_form.html', ctx)


class ProductDeleteView(StaffMemberOnlyMixin, DeleteView):
    model = Product
    template_name = 'dashboard/product/product_confirm_delete.html'
    success_url = reverse_lazy('dashboard:products')

    def post(self, request, *args, **kwargs):
        result = self.delete(request, *args, **kwargs)
        messages.success(request, _('Deleted product %s') % self.object)
        return result


@staff_member_required
def product_image_edit(request, product_pk, img_pk=None):
    product = get_object_or_404(Product, pk=product_pk)
    if img_pk:
        product_image = get_object_or_404(product.images, pk=img_pk)
        title = product_image.image.name
    else:
        product_image = ProductImage(product=product)
        title = _('Add image')
    form = ProductImageForm(request.POST or None, request.FILES or None,
                            instance=product_image)
    if form.is_valid():
        product_image = form.save()
        if img_pk:
            msg = _('Updated image %s') % product_image.image.name
        else:
            msg = _('Added image %s') % product_image.image.name
        messages.success(request, msg)
        success_url = request.POST['success_url']
        return redirect(success_url)
    else:
        if form.errors:
            messages.error(request, _('Your submitted data was not valid - '
                                      'please correct the errors below'))
    ctx = {'product': product, 'product_image': product_image, 'title': title, 'form': form}
    return TemplateResponse(request, 'dashboard/product/product_image_form.html', ctx)


@staff_member_required
def product_image_delete(request, product_pk, img_pk):
    product = get_object_or_404(Product, pk=product_pk)
    product_image = get_object_or_404(product.images, pk=img_pk)
    if request.method == 'POST':
        product_image.delete()
        messages.success(request, _('Deleted image %s') % product_image.image.name)
        success_url = request.POST['success_url']
        return redirect(success_url)
    ctx = {'product': product, 'product_image': product_image}
    return TemplateResponse(request, 'dashboard/product/product_image_confirm_delete.html', ctx)
