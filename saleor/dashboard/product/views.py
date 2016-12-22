from __future__ import unicode_literals

from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from . import forms
from ...core.utils import get_paginator_items
from ...product.models import (Product, ProductAttribute, ProductClass,
                               ProductImage, ProductVariant, Stock,
                               StockLocation)
from ..views import staff_member_required


@staff_member_required
def product_class_list(request):
    classes = ProductClass.objects.all().prefetch_related(
        'product_attributes', 'variant_attributes')
    form = forms.ProductClassForm(request.POST or None)
    if form.is_valid():
        return redirect('dashboard:product-class-add')
    classes = get_paginator_items(classes, 30, request.GET.get('page'))
    classes.object_list = [
        (pc.pk, pc.name, pc.has_variants, pc.product_attributes.all(),
         pc.variant_attributes.all())
        for pc in classes.object_list]
    ctx = {'form': form, 'product_classes': classes}
    return TemplateResponse(request, 'dashboard/product/class_list.html', ctx)


@staff_member_required
def product_class_create(request):
    product_class = ProductClass()
    form = forms.ProductClassForm(request.POST or None,
                                  instance=product_class)
    if form.is_valid():
        product_class = form.save()
        msg = _('Added product type %s') % product_class
        messages.success(request, msg)
        return redirect('dashboard:product-class-list')
    ctx = {'form': form, 'product_class': product_class}
    return TemplateResponse(
        request, 'dashboard/product/product_class_form.html', ctx)


@staff_member_required
def product_class_edit(request, pk):
    product_class = get_object_or_404(
        ProductClass, pk=pk)
    form = forms.ProductClassForm(request.POST or None,
                                  instance=product_class)
    if form.is_valid():
        product_class = form.save()
        msg = _('Updated product type %s') % product_class
        messages.success(request, msg)
        return redirect('dashboard:product-class-update', pk=pk)
    ctx = {'form': form, 'product_class': product_class}
    return TemplateResponse(
        request, 'dashboard/product/product_class_form.html', ctx)


@staff_member_required
def product_class_delete(request, pk):
    product_class = get_object_or_404(ProductClass, pk=pk)
    products = [str(p) for p in product_class.products.all()]
    if request.method == 'POST':
        product_class.delete()
        messages.success(request,
                         _('Deleted product type %s') % product_class)
        return redirect('dashboard:product-class-list')
    return TemplateResponse(
        request,
        'dashboard/product/modal_product_class_confirm_delete.html',
        {'product_class': product_class, 'products': products})


@staff_member_required
def product_list(request):
    products = Product.objects.prefetch_related('images')
    product_classes = ProductClass.objects.all()
    form = forms.ProductClassSelectorForm(
        request.POST or None, product_classes=product_classes)
    if form.is_valid():
        return redirect('dashboard:product-add',
                        class_pk=form.cleaned_data['product_cls'])
    products = get_paginator_items(products, 30, request.GET.get('page'))
    ctx = {'form': form, 'products': products,
           'product_classes': product_classes}
    return TemplateResponse(request, 'dashboard/product/list.html', ctx)


@staff_member_required
def product_create(request, class_pk):
    product_class = get_object_or_404(ProductClass, pk=class_pk)
    create_variant = not product_class.has_variants
    product = Product()
    product.product_class = product_class
    product_form = forms.ProductForm(request.POST or None, instance=product)
    if create_variant:
        variant = ProductVariant(product=product)
        variant_form = forms.ProductVariantForm(request.POST or None,
                                                instance=variant,
                                                prefix='variant')
        variant_errors = not variant_form.is_valid()
    else:
        variant_form = None
        variant_errors = False

    if product_form.is_valid() and not variant_errors:
        product = product_form.save()
        if create_variant:
            variant.product = product
            variant_form.save()
        msg = _('Added product %s') % product
        messages.success(request, msg)
        return redirect('dashboard:product-update',
                        pk=product.pk)

    ctx = {'product_form': product_form, 'variant_form': variant_form,
           'product': product}
    return TemplateResponse(
        request, 'dashboard/product/product_form.html', ctx)


@staff_member_required
def product_edit(request, pk):
    product = get_object_or_404(
        Product.objects.prefetch_related(
            'images', 'variants'), pk=pk)
    edit_variant = not product.product_class.has_variants
    attributes = product.product_class.variant_attributes.prefetch_related(
        'values')
    images = product.images.all()
    variants = product.variants.all()
    stock_items = Stock.objects.filter(
        variant__in=variants).select_related('variant')

    form = forms.ProductForm(request.POST or None, instance=product)
    variants_delete_form = forms.VariantBulkDeleteForm()
    stock_delete_form = forms.StockBulkDeleteForm()

    if edit_variant:
        variant = variants.first()
        variant_form = forms.ProductVariantForm(
            request.POST or None, instance=variant, prefix='variant')
        variant_errors = not variant_form.is_valid()
    else:
        variant_form = None
        variant_errors = False

    if form.is_valid() and not variant_errors:
        product = form.save()
        msg = _('Updated product %s') % product
        messages.success(request, msg)
        return redirect('dashboard:product-update', pk=product.pk)
    ctx = {'attributes': attributes, 'images': images, 'product_form': form,
           'product': product, 'stock_delete_form': stock_delete_form,
           'stock_items': stock_items, 'variants': variants,
           'variants_delete_form': variants_delete_form,
           'variant_form': variant_form}
    return TemplateResponse(
        request, 'dashboard/product/product_form.html', ctx)


@staff_member_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, _('Deleted product %s') % product)
        return redirect('dashboard:product-list')
    return TemplateResponse(
        request, 'dashboard/product/modal_product_confirm_delete.html',
        {'product': product})


@staff_member_required
def stock_edit(request, product_pk, stock_pk=None):
    product = get_object_or_404(Product, pk=product_pk)
    if stock_pk:
        stock = get_object_or_404(Stock, pk=stock_pk)
    else:
        stock = Stock()
    form = forms.StockForm(request.POST or None, instance=stock,
                           product=product)
    if form.is_valid():
        form.save()
        messages.success(request, _('Saved stock'))
        product_url = reverse(
            'dashboard:product-update', kwargs={'pk': product_pk})
        success_url = request.POST.get('success_url', product_url)
        if is_safe_url(success_url, request.get_host()):
            return redirect(success_url)
    ctx = {'form': form, 'product': product, 'stock': stock}
    return TemplateResponse(request, 'dashboard/product/stock_form.html', ctx)


@staff_member_required
def stock_delete(request, product_pk, stock_pk):
    product = get_object_or_404(Product, pk=product_pk)
    stock = get_object_or_404(Stock, pk=stock_pk)
    if request.method == 'POST':
        stock.delete()
        messages.success(request, _('Deleted stock'))
        success_url = request.POST['success_url']
        if is_safe_url(success_url, request.get_host()):
            return redirect(success_url)
    ctx = {'product': product, 'stock': stock}
    return TemplateResponse(
        request, 'dashboard/product/stock_confirm_delete.html', ctx)


@staff_member_required
@require_http_methods(['POST'])
def stock_bulk_delete(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    form = forms.StockBulkDeleteForm(request.POST)
    if form.is_valid():
        form.delete()
        success_url = request.POST['success_url']
        messages.success(request, _('Deleted stock'))
        if is_safe_url(success_url, request.get_host()):
            return redirect(success_url)
    return redirect('dashboard:product-update', pk=product.pk)


@staff_member_required
def product_image_edit(request, product_pk, img_pk=None):
    product = get_object_or_404(Product, pk=product_pk)
    if img_pk:
        product_image = get_object_or_404(product.images, pk=img_pk)
    else:
        product_image = ProductImage(product=product)
    show_variants = product.product_class.has_variants
    form = forms.ProductImageForm(request.POST or None, request.FILES or None,
                                  instance=product_image)
    if form.is_valid():
        product_image = form.save()
        if img_pk:
            msg = _('Updated image %s') % product_image.image.name
        else:
            msg = _('Added image %s') % product_image.image.name
        messages.success(request, msg)
        success_url = request.POST['success_url']
        if is_safe_url(success_url, request.get_host()):
            return redirect(success_url)
    ctx = {'form': form, 'product': product, 'product_image': product_image,
           'show_variants': show_variants}
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
        if is_safe_url(success_url, request.get_host()):
            return redirect(success_url)
    ctx = {'product': product, 'product_image': product_image}
    return TemplateResponse(
        request,
        'dashboard/product/modal_product_image_confirm_delete.html', ctx)


@staff_member_required
def variant_edit(request, product_pk, variant_pk=None):
    product = get_object_or_404(Product.objects.all(),
                                pk=product_pk)
    form_initial = {}
    if variant_pk:
        variant = get_object_or_404(product.variants.all(),
                                    pk=variant_pk)
    else:
        variant = ProductVariant(product=product)
    form = forms.ProductVariantForm(request.POST or None, instance=variant,
                                    initial=form_initial)
    attribute_form = forms.VariantAttributeForm(request.POST or None,
                                                instance=variant)
    if all([form.is_valid(), attribute_form.is_valid()]):
        form.save()
        attribute_form.save()
        if variant_pk:
            msg = _('Updated variant %s') % variant.name
        else:
            msg = _('Added variant %s') % variant.name
        messages.success(request, msg)
        success_url = request.POST['success_url']
        if is_safe_url(success_url, request.get_host()):
            return redirect(success_url)
    ctx = {'attribute_form': attribute_form, 'form': form, 'product': product,
           'variant': variant}
    return TemplateResponse(
        request, 'dashboard/product/variant_form.html', ctx)


@staff_member_required
def variant_delete(request, product_pk, variant_pk):
    product = get_object_or_404(Product, pk=product_pk)
    variant = get_object_or_404(product.variants, pk=variant_pk)
    is_only_variant = product.variants.count() == 1
    if request.method == 'POST':
        variant.delete()
        messages.success(request, _('Deleted variant %s') % variant.name)
        success_url = request.POST['success_url']
        if is_safe_url(success_url, request.get_host()):
            return redirect(success_url)
    ctx = {'is_only_variant': is_only_variant, 'product': product,
           'variant': variant}
    return TemplateResponse(
        request,
        'dashboard/product/modal_product_variant_confirm_delete.html', ctx)


@staff_member_required
@require_http_methods(['POST'])
def variants_bulk_delete(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    form = forms.VariantBulkDeleteForm(request.POST)
    if form.is_valid():
        form.delete()
        success_url = request.POST['success_url']
        messages.success(request, _('Deleted variants'))
        if is_safe_url(success_url, request.get_host()):
            return redirect(success_url)
    return redirect('dashboard:product-update', pk=product.pk)


@staff_member_required
def attribute_list(request):
    attributes = [
        (attribute.pk, attribute.display, attribute.values.all())
        for attribute in ProductAttribute.objects.prefetch_related('values')]
    ctx = {'attributes': attributes}
    return TemplateResponse(request, 'dashboard/product/attributes/list.html',
                            ctx)


@staff_member_required
def attribute_edit(request, pk=None):
    if pk:
        attribute = get_object_or_404(ProductAttribute, pk=pk)
    else:
        attribute = ProductAttribute()
    form = forms.ProductAttributeForm(request.POST or None, instance=attribute)
    formset = forms.AttributeChoiceValueFormset(request.POST or None,
                                                request.FILES or None,
                                                instance=attribute)
    if all([form.is_valid(), formset.is_valid()]):
        attribute = form.save()
        formset.save()
        msg = _('Updated attribute') if pk else _('Added attribute')
        messages.success(request, msg)
        return redirect('dashboard:product-attribute-update', pk=attribute.pk)
    ctx = {'attribute': attribute, 'form': form, 'formset': formset}
    return TemplateResponse(request, 'dashboard/product/attributes/form.html',
                            ctx)


@staff_member_required
def attribute_delete(request, pk):
    attribute = get_object_or_404(ProductAttribute, pk=pk)
    if request.method == 'POST':
        attribute.delete()
        messages.success(
            request, _('Deleted attribute %s') % (attribute.display,))
        return redirect('dashboard:product-attributes')
    ctx = {'attribute': attribute}
    return TemplateResponse(
        request, 'dashboard/product/attributes/modal_confirm_delete.html', ctx)


@staff_member_required
def stock_location_list(request):
    stock_locations = StockLocation.objects.all()
    ctx = {'locations': stock_locations}
    return TemplateResponse(
        request, 'dashboard/product/stock_locations/list.html', ctx)


@staff_member_required
def stock_location_edit(request, location_pk=None):
    if location_pk:
        location = get_object_or_404(StockLocation, pk=location_pk)
    else:
        location = StockLocation()
    form = forms.StockLocationForm(request.POST or None, instance=location)
    if form.is_valid():
        form.save()
        msg = _('Updated location') if location_pk else _('Added location')
        messages.success(request, msg)
        return redirect('dashboard:product-stock-location-list')
    ctx = {'form': form, 'location': location}
    return TemplateResponse(
        request, 'dashboard/product/stock_locations/form.html', ctx)


@staff_member_required
def stock_location_delete(request, location_pk):
    location = get_object_or_404(StockLocation, pk=location_pk)
    stock_count = location.stock_set.count()
    if request.method == 'POST':
        location.delete()
        messages.success(
            request, _('Deleted location %s') % location)
        return redirect('dashboard:product-stock-location-list')
    ctx = {'location': location, 'stock_count': stock_count}
    return TemplateResponse(
        request, 'dashboard/product/stock_locations/modal_confirm_delete.html',
        ctx)
