from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from django.utils.translation import pgettext_lazy
from django.views.decorators.http import require_POST

from ...core.utils import get_paginator_items
from ...product.models import (
    Product, ProductAttribute, ProductClass, ProductImage, ProductVariant,
    Stock, StockLocation)
from ...product.utils import get_availability
from ..views import staff_member_required, superuser_required
from ...settings import DASHBOARD_PAGINATE_BY
from . import forms


@superuser_required
def product_class_list(request):
    classes = ProductClass.objects.all().prefetch_related(
        'product_attributes', 'variant_attributes').order_by('name')
    form = forms.ProductClassForm(request.POST or None)
    if form.is_valid():
        return redirect('dashboard:product-class-add')
    classes = get_paginator_items(
        classes, DASHBOARD_PAGINATE_BY, request.GET.get('page'))
    classes.object_list = [
        (pc.pk, pc.name, pc.has_variants, pc.product_attributes.all(),
         pc.variant_attributes.all())
        for pc in classes.object_list]
    ctx = {'form': form, 'product_classes': classes}
    return TemplateResponse(
        request,
        'dashboard/product/product_class/list.html',
        ctx)


@superuser_required
def product_class_create(request):
    product_class = ProductClass()
    form = forms.ProductClassForm(request.POST or None,
                                  instance=product_class)
    if form.is_valid():
        product_class = form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added product type %s') % product_class
        messages.success(request, msg)
        return redirect('dashboard:product-class-list')
    ctx = {'form': form, 'product_class': product_class}
    return TemplateResponse(
        request,
        'dashboard/product/product_class/form.html',
        ctx)


@superuser_required
def product_class_edit(request, pk):
    product_class = get_object_or_404(
        ProductClass, pk=pk)
    form = forms.ProductClassForm(request.POST or None,
                                  instance=product_class)
    if form.is_valid():
        product_class = form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated product type %s') % product_class
        messages.success(request, msg)
        return redirect('dashboard:product-class-update', pk=pk)
    ctx = {'form': form, 'product_class': product_class}
    return TemplateResponse(
        request,
        'dashboard/product/product_class/form.html',
        ctx)


@superuser_required
def product_class_delete(request, pk):
    product_class = get_object_or_404(ProductClass, pk=pk)
    if request.method == 'POST':
        product_class.delete()
        messages.success(
            request,
            pgettext_lazy(
                'Dashboard message',
                'Deleted product type %s') % product_class)
        return redirect('dashboard:product-class-list')
    ctx = {'product_class': product_class,
           'products': product_class.products.all()}
    return TemplateResponse(
        request,
        'dashboard/product/product_class/modal/confirm_delete.html',
        ctx)


@staff_member_required
@permission_required('product.view_product')
def product_list(request):
    products = Product.objects.prefetch_related('images')
    products = products.order_by('name')
    product_classes = ProductClass.objects.all()
    form = forms.ProductClassSelectorForm(
        request.POST or None, product_classes=product_classes)
    if form.is_valid():
        return redirect(
            'dashboard:product-add', class_pk=form.cleaned_data['product_cls'])
    products = get_paginator_items(
        products, DASHBOARD_PAGINATE_BY, request.GET.get('page'))
    ctx = {
        'form': form, 'products': products, 'product_classes': product_classes}
    return TemplateResponse(request, 'dashboard/product/list.html', ctx)


@staff_member_required
@permission_required('product.edit_product')
def product_create(request, class_pk):
    product_class = get_object_or_404(ProductClass, pk=class_pk)
    create_variant = not product_class.has_variants
    product = Product()
    product.product_class = product_class
    product_form = forms.ProductForm(request.POST or None, instance=product)
    if create_variant:
        variant = ProductVariant(product=product)
        variant_form = forms.ProductVariantForm(
            request.POST or None, instance=variant, prefix='variant')
        variant_errors = not variant_form.is_valid()
    else:
        variant_form = None
        variant_errors = False

    if product_form.is_valid() and not variant_errors:
        product = product_form.save()
        if create_variant:
            variant.product = product
            variant_form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Added product %s') % product
        messages.success(request, msg)
        return redirect('dashboard:product-detail', pk=product.pk)
    ctx = {
        'product_form': product_form, 'variant_form': variant_form,
        'product': product}
    return TemplateResponse(request, 'dashboard/product/form.html', ctx)


@staff_member_required
@permission_required('product.view_product')
def product_detail(request, pk):
    products = Product.objects.prefetch_related(
        'variants__stock', 'images',
        'product_class__variant_attributes__values').all()
    product = get_object_or_404(products, pk=pk)
    variants = product.variants.all()
    images = product.images.all()
    availability = get_availability(product)
    sale_price = availability.price_range
    gross_price_range = product.get_gross_price_range()

    # no_variants is True for product classes that doesn't require variant.
    # In this case we're using the first variant under the hood to allow stock
    # management.
    no_variants = not product.product_class.has_variants
    only_variant = variants.first() if no_variants else None
    if only_variant:
        stock = only_variant.stock.all()
    else:
        stock = Stock.objects.none()
    ctx = {
        'product': product, 'sale_price': sale_price, 'variants': variants,
        'gross_price_range': gross_price_range, 'images': images,
        'no_variants': no_variants, 'only_variant': only_variant,
        'stock': stock}
    return TemplateResponse(request, 'dashboard/product/detail.html', ctx)


@staff_member_required
@permission_required('product.edit_product')
def product_toggle_is_published(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_published = not product.is_published
    product.save(update_fields=['is_published'])
    return JsonResponse(
        {'success': True, 'is_published': product.is_published})


@staff_member_required
@permission_required('product.edit_product')
def product_edit(request, pk):
    product = get_object_or_404(
        Product.objects.prefetch_related('variants'), pk=pk)

    edit_variant = not product.product_class.has_variants
    form = forms.ProductForm(request.POST or None, instance=product)

    if edit_variant:
        variant = product.variants.first()
        variant_form = forms.ProductVariantForm(
            request.POST or None, instance=variant, prefix='variant')
        variant_errors = not variant_form.is_valid()
    else:
        variant_form = None
        variant_errors = False

    if form.is_valid() and not variant_errors:
        product = form.save()
        if edit_variant:
            variant_form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated product %s') % product
        messages.success(request, msg)
        return redirect('dashboard:product-detail', pk=product.pk)
    ctx = {'product': product, 'product_form': form,
           'variant_form': variant_form}
    return TemplateResponse(request, 'dashboard/product/form.html', ctx)


@staff_member_required
@permission_required('product.edit_product')
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(
            request,
            pgettext_lazy('Dashboard message', 'Deleted product %s') % product)
        return redirect('dashboard:product-list')
    return TemplateResponse(
        request,
        'dashboard/product/modal/confirm_delete.html',
        {'product': product})


@staff_member_required
@permission_required('product.view_stock_location')
def stock_details(request, product_pk, variant_pk, stock_pk):
    product = get_object_or_404(Product, pk=product_pk)
    variant = get_object_or_404(product.variants, pk=variant_pk)
    stock = get_object_or_404(variant.stock, pk=stock_pk)
    ctx = {'stock': stock, 'product': product, 'variant': variant}
    return TemplateResponse(
        request,
        'dashboard/product/stock/detail.html',
        ctx)


@staff_member_required
@permission_required('product.edit_stock_location')
def stock_edit(request, product_pk, variant_pk, stock_pk=None):
    product = get_object_or_404(Product, pk=product_pk)
    variant = get_object_or_404(product.variants, pk=variant_pk)
    if stock_pk:
        stock = get_object_or_404(variant.stock, pk=stock_pk)
    else:
        stock = Stock()
    form = forms.StockForm(
        request.POST or None, instance=stock, variant=variant)
    if form.is_valid():
        form.save()
        messages.success(
            request, pgettext_lazy('Dashboard message', 'Saved stock'))
        return redirect(
            'dashboard:variant-details', product_pk=product.pk,
            variant_pk=variant.pk)
    ctx = {'form': form, 'product': product,
           'variant': variant, 'stock': stock}
    return TemplateResponse(
        request,
        'dashboard/product/stock/form.html',
        ctx)


@staff_member_required
@permission_required('product.edit_stock_location')
def stock_delete(request, product_pk, variant_pk, stock_pk):
    product = get_object_or_404(Product, pk=product_pk)
    variant = get_object_or_404(product.variants, pk=variant_pk)
    stock = get_object_or_404(Stock, pk=stock_pk)
    if request.method == 'POST':
        stock.delete()
        messages.success(
            request, pgettext_lazy('Dashboard message', 'Deleted stock'))
        return redirect(
            'dashboard:variant-details', product_pk=product.pk,
            variant_pk=variant.pk)
    ctx = {'product': product, 'stock': stock, 'variant': variant}
    return TemplateResponse(
        request,
        'dashboard/product/stock/modal/confirm_delete.html',
        ctx)


@staff_member_required
@permission_required('product.view_product')
def product_images(request, product_pk):
    product = get_object_or_404(
        Product.objects.prefetch_related('images'), pk=product_pk)
    images = product.images.all()
    return TemplateResponse(
        request,
        'dashboard/product/product_image/list.html',
        {'product': product, 'images': images})


@staff_member_required
@permission_required('product.edit_product')
def product_image_edit(request, product_pk, img_pk=None):
    product = get_object_or_404(Product, pk=product_pk)
    if img_pk:
        product_image = get_object_or_404(product.images, pk=img_pk)
    else:
        product_image = ProductImage(product=product)
    form = forms.ProductImageForm(
        request.POST or None, request.FILES or None, instance=product_image)
    if form.is_valid():
        product_image = form.save()
        if img_pk:
            msg = pgettext_lazy(
                'Dashboard message',
                'Updated image %s') % product_image.image.name
        else:
            msg = pgettext_lazy(
                'Dashboard message',
                'Added image %s') % product_image.image.name
        messages.success(request, msg)
        return redirect('dashboard:product-image-list', product_pk=product.pk)
    ctx = {'form': form, 'product': product, 'product_image': product_image}
    return TemplateResponse(
        request,
        'dashboard/product/product_image/form.html',
        ctx)


@staff_member_required
@permission_required('product.edit_product')
def product_image_delete(request, product_pk, img_pk):
    product = get_object_or_404(Product, pk=product_pk)
    image = get_object_or_404(product.images, pk=img_pk)
    if request.method == 'POST':
        image.delete()
        messages.success(
            request,
            pgettext_lazy(
                'Dashboard message',
                'Deleted image %s') % image.image.name)
        return redirect('dashboard:product-image-list', product_pk=product.pk)
    return TemplateResponse(
        request,
        'dashboard/product/product_image/modal/confirm_delete.html',
        {'product': product, 'image': image})


@staff_member_required
@permission_required('product.edit_product')
def variant_edit(request, product_pk, variant_pk=None):
    product = get_object_or_404(
        Product.objects.all(), pk=product_pk)
    if variant_pk:
        variant = get_object_or_404(product.variants.all(), pk=variant_pk)
    else:
        variant = ProductVariant(product=product)
    form = forms.ProductVariantForm(request.POST or None, instance=variant)
    attribute_form = forms.VariantAttributeForm(
        request.POST or None, instance=variant)
    if all([form.is_valid(), attribute_form.is_valid()]):
        form.save()
        attribute_form.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Saved variant %s') % variant.name
        messages.success(request, msg)
        return redirect(
            'dashboard:variant-details', product_pk=product.pk,
            variant_pk=variant.pk)
    ctx = {'attribute_form': attribute_form, 'form': form, 'product': product,
           'variant': variant}
    return TemplateResponse(
        request,
        'dashboard/product/product_variant/form.html',
        ctx)


@staff_member_required
@permission_required('product.view_product')
def variant_details(request, product_pk, variant_pk):
    product = get_object_or_404(Product, pk=product_pk)
    qs = product.variants.prefetch_related(
        'stock__location',
        'product__product_class__variant_attributes__values')
    variant = get_object_or_404(qs, pk=variant_pk)

    # If the product class of this product assumes no variants, redirect to
    # product details page that has special UI for products without variants.

    if not product.product_class.has_variants:
        return redirect('dashboard:product-detail', pk=product.pk)

    stock = variant.stock.all()
    images = variant.images.all()
    ctx = {'images': images, 'product': product, 'stock': stock,
           'variant': variant}
    return TemplateResponse(
        request,
        'dashboard/product/product_variant/detail.html',
        ctx)


@staff_member_required
@permission_required('product.view_product')
def variant_images(request, product_pk, variant_pk):
    product = get_object_or_404(Product, pk=product_pk)
    qs = product.variants.prefetch_related('images')
    variant = get_object_or_404(qs, pk=variant_pk)
    form = forms.VariantImagesSelectForm(request.POST or None, variant=variant)
    if form.is_valid():
        form.save()
        return redirect(
            'dashboard:variant-details', product_pk=product.pk,
            variant_pk=variant.pk)
    ctx = {'form': form, 'product': product, 'variant': variant}
    return TemplateResponse(
        request,
        'dashboard/product/product_variant/modal/select_images.html',
        ctx)


@staff_member_required
@permission_required('product.edit_product')
def variant_delete(request, product_pk, variant_pk):
    product = get_object_or_404(Product, pk=product_pk)
    variant = get_object_or_404(product.variants, pk=variant_pk)
    if request.method == 'POST':
        variant.delete()
        messages.success(
            request,
            pgettext_lazy(
                'Dashboard message', 'Deleted variant %s') % variant.name)
        return redirect('dashboard:product-detail', pk=product.pk)

    ctx = {'is_only_variant': product.variants.count() == 1,
           'product': product,
           'variant': variant}
    return TemplateResponse(
        request,
        'dashboard/product/product_variant/modal/confirm_delete.html',
        ctx)


@superuser_required
def attribute_list(request):
    attributes = [
        (attribute.pk, attribute.name, attribute.values.all())
        for attribute in ProductAttribute.objects.prefetch_related('values')]
    attributes = get_paginator_items(
        attributes, DASHBOARD_PAGINATE_BY, request.GET.get('page'))
    ctx = {'attributes': attributes}
    return TemplateResponse(
        request,
        'dashboard/product/product_attribute/list.html',
        ctx)


@superuser_required
def attribute_detail(request, pk):
    attributes = ProductAttribute.objects.prefetch_related('values').all()
    attribute = get_object_or_404(attributes, pk=pk)
    return TemplateResponse(
        request,
        'dashboard/product/product_attribute/detail.html',
        {'attribute': attribute})


@superuser_required
def attribute_edit(request, pk=None):
    if pk:
        attribute = get_object_or_404(ProductAttribute, pk=pk)
    else:
        attribute = ProductAttribute()
    form = forms.ProductAttributeForm(request.POST or None, instance=attribute)
    formset = forms.AttributeChoiceValueFormset(
        request.POST or None, request.FILES or None, instance=attribute)
    if all([form.is_valid(), formset.is_valid()]):
        attribute = form.save()
        formset.save()
        msg = pgettext_lazy(
            'Dashboard message', 'Updated attribute') if pk else pgettext_lazy(
                'Dashboard message', 'Added attribute')
        messages.success(request, msg)
        return redirect('dashboard:product-attribute-detail', pk=attribute.pk)
    ctx = {'attribute': attribute, 'form': form, 'formset': formset}
    return TemplateResponse(
        request,
        'dashboard/product/product_attribute/form.html',
        ctx)


@superuser_required
def attribute_delete(request, pk):
    attribute = get_object_or_404(ProductAttribute, pk=pk)
    if request.method == 'POST':
        attribute.delete()
        messages.success(
            request,
            pgettext_lazy(
                'Dashboard message',
                'Deleted attribute %s') % (attribute.name,))
        return redirect('dashboard:product-attributes')
    return TemplateResponse(
        request,
        'dashboard/product/product_attribute/modal/confirm_delete.html',
        {'attribute': attribute})


@staff_member_required
@permission_required('product.view_stock_location')
def stock_location_list(request):
    stock_locations = StockLocation.objects.all().order_by('name')
    stock_locations = get_paginator_items(
        stock_locations, DASHBOARD_PAGINATE_BY, request.GET.get('page'))
    ctx = {'locations': stock_locations}
    return TemplateResponse(
        request,
        'dashboard/product/stock_location/list.html',
        ctx)


@staff_member_required
@permission_required('product.edit_stock_location')
def stock_location_edit(request, location_pk=None):
    if location_pk:
        location = get_object_or_404(StockLocation, pk=location_pk)
    else:
        location = StockLocation()
    form = forms.StockLocationForm(request.POST or None, instance=location)
    if form.is_valid():
        form.save()
        msg = pgettext_lazy(
            'Dashboard message for stock location',
            'Updated location') if location_pk else pgettext_lazy(
                'Dashboard message for stock location', 'Added location')
        messages.success(request, msg)
        return redirect('dashboard:product-stock-location-list')
    return TemplateResponse(
        request,
        'dashboard/product/stock_location/form.html',
        {'form': form, 'location': location})


@staff_member_required
@permission_required('product.edit_stock_location')
def stock_location_delete(request, location_pk):
    location = get_object_or_404(StockLocation, pk=location_pk)
    stock_count = location.stock_set.count()
    if request.method == 'POST':
        location.delete()
        messages.success(
            request, pgettext_lazy(
                'Dashboard message for stock location',
                'Deleted location %s') % location)
        return redirect('dashboard:product-stock-location-list')
    ctx = {'location': location, 'stock_count': stock_count}
    return TemplateResponse(
        request,
        'dashboard/product/stock_location/modal/confirm_delete.html',
        ctx)


@require_POST
@staff_member_required
def ajax_reorder_product_images(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    form = forms.ReorderProductImagesForm(request.POST, instance=product)
    status = 200
    ctx = {}
    if form.is_valid():
        form.save()
    elif form.errors:
        status = 400
        ctx = {'error': form.errors}
    return JsonResponse(ctx, status=status)


@require_POST
@staff_member_required
def ajax_upload_image(request, product_pk):
    product = get_object_or_404(Product, pk=product_pk)
    form = forms.UploadImageForm(
        request.POST or None, request.FILES or None, product=product)
    status = 200
    if form.is_valid():
        image = form.save()
        ctx = {'id': image.pk, 'image': None, 'order': image.order}
    elif form.errors:
        status = 400
        ctx = {'error': form.errors}
    return JsonResponse(ctx, status=status)
