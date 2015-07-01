from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView

from ...product.models import Product, ProductImage, Stock, ProductAttribute
from ..utils import paginate
from ..views import StaffMemberOnlyMixin, staff_member_required
from .forms import (ProductClassForm, get_product_form,
                    get_product_cls_by_name, get_variant_form,
                    ProductImageForm, get_verbose_name, StockForm,
                    get_variant_cls, ProductAttributeForm,
                    AttributeChoiceValueFormset, VariantAttributesForm,
                    VariantsBulkDeleteForm)


@staff_member_required
def product_list(request):
    products = Product.objects.prefetch_related('images')
    form = ProductClassForm(request.POST or None)
    if form.is_valid():
        product_cls = form.cleaned_data['product_cls']
        return redirect('dashboard:product-add', product_cls=product_cls)
    products, paginator = paginate(products, 30, request.GET.get('page'))
    ctx = {'products': products, 'form': form, 'paginator': paginator}
    return TemplateResponse(request, 'dashboard/product/list.html', ctx)


@staff_member_required
def product_details(request, pk=None, product_cls=None):
    creating = pk is None
    initial = {}
    if creating:
        product = get_product_cls_by_name(product_cls)()
        title = _('Add new %s') % get_verbose_name(product)
    else:
        product = get_object_or_404(
            Product.objects.select_subclasses().prefetch_related(
                'images', 'variants'), pk=pk)
        title = product.name
    attributes = product.attributes.all()
    images = product.images.all()
    variants = product.variants.select_subclasses()
    stock_items = Stock.objects.filter(variant__in=variants)

    form_cls = get_product_form(product)
    form = form_cls(instance=product, initial=initial)
    variants_delete_form = VariantsBulkDeleteForm(product=product)

    if 'product-form' in request.POST:
        form = form_cls(request.POST, instance=product)
        product = save_product_form(request, form, creating)
        if creating and product:
            return redirect('dashboard:product-update', pk=product.pk)

    if 'variants-bulk-delete-form' in request.POST:
        variants_delete_form = VariantsBulkDeleteForm(request.POST, product=product)
        if variants_delete_form.is_valid():
            variants_delete_form.delete()
            return redirect('dashboard:product-update', pk=product.pk)

    ctx = {
        'attributes': attributes, 'title': title, 'product': product,
        'images': images, 'product_form': form, 'stock_items': stock_items,
        'variants': variants, 'variants_delete_form': variants_delete_form}
    if pk:
        images_reorder_url = reverse_lazy('dashboard:product-images-reorder',
                                          kwargs={'product_pk': pk})
        ctx['images_reorder_url'] = images_reorder_url
    return TemplateResponse(request, 'dashboard/product/product_form.html', ctx)


def save_product_form(request, form, creating):
    product = None
    if form.is_valid():
        product = form.save()
        if creating:
            msg = _('Added product %s') % product
        else:
            msg = _('Updated product %s') % product
        messages.success(request, msg)
    else:
        if form.errors:
            messages.error(request, _('Your submitted data was not valid - '
                                      'please correct the errors below'))
    return product


class ProductDeleteView(StaffMemberOnlyMixin, DeleteView):
    model = Product
    template_name = 'dashboard/product/product_confirm_delete.html'
    success_url = reverse_lazy('dashboard:products')

    def post(self, request, *args, **kwargs):
        result = self.delete(request, *args, **kwargs)
        messages.success(request, _('Deleted product %s') % self.object)
        return result


@staff_member_required
def stock_edit(request, product_pk, stock_pk=None):
    product = get_object_or_404(Product, pk=product_pk)
    if stock_pk:
        stock = get_object_or_404(Stock, pk=stock_pk)
    else:
        stock = Stock()
    form = StockForm(request.POST or None, instance=stock, product=product)
    if product.variants.exists():
        if form.is_valid():
            form.save()
            messages.success(request, _('Saved stock'))
            success_url = request.POST['success_url']
            return redirect(success_url)
        else:
            if form.errors:
                messages.error(request, _('Your submitted data was not valid - '
                                          'please correct the errors below'))
    else:
        messages.error(request, _(
            'You have to add at least one variant before you can add stock'))
    ctx = {'product': product, 'stock': stock, 'form': form}
    return TemplateResponse(request, 'dashboard/product/stock_form.html', ctx)


@staff_member_required
def stock_delete(request, product_pk, stock_pk):
    product = get_object_or_404(Product, pk=product_pk)
    stock = get_object_or_404(Stock, pk=stock_pk)
    if request.method == 'POST':
        stock.delete()
        messages.success(request, _('Deleted stock'))
        success_url = request.POST['success_url']
        return redirect(success_url)
    ctx = {'product': product, 'stock': stock}
    return TemplateResponse(
        request, 'dashboard/product/stock_confirm_delete.html', ctx)


@staff_member_required
def product_image_edit(request, product_pk, img_pk=None):
    product = get_object_or_404(Product, pk=product_pk)
    if img_pk:
        product_image = get_object_or_404(product.images, pk=img_pk)
    else:
        product_image = ProductImage(product=product)
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
    ctx = {'product': product, 'product_image': product_image,
           'form': form}
    return TemplateResponse(
        request, 'dashboard/product/product_image_form.html', ctx)


@staff_member_required
def product_image_delete(request, product_pk, img_pk):
    product = get_object_or_404(Product, pk=product_pk)
    product_image = get_object_or_404(product.images, pk=img_pk)
    if request.method == 'POST':
        product_image.delete()
        messages.success(
            request, _('Deleted image %s') % product_image.image.name)
        success_url = request.POST['success_url']
        return redirect(success_url)
    ctx = {'product': product, 'product_image': product_image}
    return TemplateResponse(
        request, 'dashboard/product/product_image_confirm_delete.html', ctx)


@staff_member_required
def variant_edit(request, product_pk, variant_pk=None):
    product = get_object_or_404(Product.objects.select_subclasses(),
                                pk=product_pk)
    variant_cls = get_variant_cls(product)
    form_initial = {}
    if variant_pk:
        variant = get_object_or_404(product.variants.select_subclasses(),
                                    pk=variant_pk)
    else:
        variant = variant_cls(product=product)

    form_cls = get_variant_form(product)
    form = form_cls(request.POST or None, instance=variant,
                    initial=form_initial)
    attributes_form = VariantAttributesForm(request.POST or None,
                                            instance=variant)
    forms = [form, attributes_form]

    if all([f.is_valid() for f in forms]):
        form.save()
        attributes_form.save()
        if variant_pk:
            msg = _('Updated variant %s') % variant.name
        else:
            msg = _('Added variant %s') % variant.name
        messages.success(request, msg)
        success_url = request.POST['success_url']
        return redirect(success_url)
    else:
        if any([f.errors for f in forms]):
            messages.error(request, _('Your submitted data was not valid - '
                                      'please correct the errors below'))
    ctx = {'product': product, 'variant': variant,
           'form': form, 'attributes_form': attributes_form}
    return TemplateResponse(request, 'dashboard/product/variant_form.html', ctx)


@staff_member_required
def variant_delete(request, product_pk, variant_pk):
    product = get_object_or_404(Product, pk=product_pk)
    variant = get_object_or_404(product.variants, pk=variant_pk)
    is_only_variant = product.variants.count() == 1
    if request.method == 'POST':
        variant.delete()
        messages.success(request, _('Deleted variant %s') % variant.name)
        success_url = request.POST['success_url']
        return redirect(success_url)
    ctx = {'product': product, 'variant': variant,
           'is_only_variant': is_only_variant}
    return TemplateResponse(
        request, 'dashboard/product/product_variant_confirm_delete.html', ctx)


@staff_member_required
def attribute_list(request):
    attributes = ProductAttribute.objects.all()
    ctx = {'attributes': attributes}
    return TemplateResponse(request, 'dashboard/product/attributes/list.html',
                            ctx)


@staff_member_required
def attribute_edit(request, pk=None):
    if pk:
        attribute = get_object_or_404(ProductAttribute, pk=pk)
        title = attribute.display
    else:
        attribute = ProductAttribute()
        title = _('Add new attribute')
    form = ProductAttributeForm(request.POST or None, instance=attribute)
    formset = AttributeChoiceValueFormset(request.POST or None,
                                          request.FILES or None,
                                          instance=attribute)
    if form.is_valid() and formset.is_valid():
        attribute = form.save()
        formset.save()
        msg = _('Updated attribute') if pk else _('Added attribute')
        messages.success(request, msg)
        return redirect('dashboard:product-attribute-update', pk=attribute.pk)
    else:
        if form.errors or formset.errors:
            messages.error(request, _('Your submitted data was not valid - '
                                      'please correct the errors below'))
    ctx = {'attribute': attribute, 'form': form, 'formset': formset, 'title': title}
    return TemplateResponse(request, 'dashboard/product/attributes/form.html',
                            ctx)


@staff_member_required
def attribute_delete(request, pk):
    attribute = get_object_or_404(ProductAttribute, pk=pk)
    if request.method == 'POST':
        attribute.delete()
        messages.success(request, _('Deleted attribute %s' % attribute.display))
        return redirect('dashboard:product-attributes')
    ctx = {'attribute': attribute}
    return TemplateResponse(request,
                            'dashboard/product/attributes/confirm_delete.html',
                            ctx)
