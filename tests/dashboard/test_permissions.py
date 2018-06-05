from django.urls import reverse

from saleor.account.models import User


def test_admin_can_view_staff_list(admin_client):
    response = admin_client.get(reverse('dashboard:staff-list'))
    assert response.status_code == 200


def test_staff_cant_view_staff_list(staff_client):
    response = staff_client.get(reverse('dashboard:staff-list'))
    assert response.status_code == 302


def test_admin_can_view_staff_details(admin_client, admin_user):
    response = admin_client.get(reverse('dashboard:staff-details',
                                        args=[admin_user.pk]))
    assert response.status_code == 200


def test_staff_cant_view_staff_details(staff_client, admin_user):
    response = staff_client.get(reverse('dashboard:staff-details',
                                        args=[admin_user.pk]))
    assert response.status_code == 302


def test_admin_can_view_staff_create(admin_client):
    response = admin_client.get(reverse('dashboard:staff-create'))
    assert response.status_code == 200


def test_staff_cant_view_staff_create(staff_client):
    response = staff_client.get(reverse('dashboard:staff-create'))
    assert response.status_code == 302


def test_admin_can_view_groups_list(admin_client):
    response = admin_client.get(reverse('dashboard:group-list'))
    assert response.status_code == 200


def test_staff_cant_view_groups_list(staff_client):
    response = staff_client.get(reverse('dashboard:group-list'))
    assert response.status_code == 302


def test_admin_can_view_group_details(admin_client, staff_group):
    response = admin_client.get(reverse('dashboard:group-details',
                                        args=[staff_group.pk]))
    assert response.status_code == 200


def test_staff_cant_view_group_details(staff_client, staff_group):
    response = staff_client.get(reverse('dashboard:group-details',
                                        args=[staff_group.pk]))
    assert response.status_code == 302


def test_admin_can_view_group_create(admin_client):
    response = admin_client.get(reverse('dashboard:group-create'))
    assert response.status_code == 200


def test_staff_cant_view_group_create(staff_client):
    response = staff_client.get(reverse('dashboard:group-create'))
    assert response.status_code == 302


def test_admin_can_view_product_types_list(admin_client):
    response = admin_client.get(reverse('dashboard:product-type-list'))
    assert response.status_code == 200


def test_staff_cant_view_product_types_list(staff_client):
    response = staff_client.get(reverse('dashboard:product-type-list'))
    assert response.status_code == 302


def test_admin_can_view_product_type_add(admin_client):
    response = admin_client.get(reverse('dashboard:product-type-add'))
    assert response.status_code == 200


def test_staff_cant_view_product_type_add(staff_client):
    response = staff_client.get(reverse('dashboard:product-type-add'))
    assert response.status_code == 302


def test_admin_can_view_product_type_update(admin_client, product_type):
    response = admin_client.get(reverse('dashboard:product-type-update',
                                        args=[product_type.pk]))
    assert response.status_code == 200


def test_staff_cant_view_product_type_update(staff_client, product_type):
    response = staff_client.get(reverse('dashboard:product-type-update',
                                        args=[product_type.pk]))
    assert response.status_code == 302


def test_admin_can_view_product_type_delete(admin_client, product_type):
    response = admin_client.get(reverse('dashboard:product-type-delete',
                                        args=[product_type.pk]))
    assert response.status_code == 200


def test_staff_cant_view_product_type_delete(staff_client, product_type):
    response = staff_client.get(reverse('dashboard:product-type-delete',
                                        args=[product_type.pk]))
    assert response.status_code == 302


def test_admin_can_view_products_attribute_list(admin_client):
    response = admin_client.get(reverse('dashboard:product-attributes'))
    assert response.status_code == 200


def test_staff_cant_view_products_attribute_list(staff_client):
    response = staff_client.get(reverse('dashboard:product-attributes'))
    assert response.status_code == 302


def test_admin_can_view_products_attribute_add(admin_client):
    response = admin_client.get(reverse('dashboard:product-attribute-add'))
    assert response.status_code == 200


def test_staff_cant_view_products_attribute_add(staff_client):
    response = staff_client.get(reverse('dashboard:product-attribute-add'))
    assert response.status_code == 302


def test_admin_can_view_products_attribute_details(
        admin_client, color_attribute):
    response = admin_client.get(reverse('dashboard:product-attribute-details',
                                        args=[color_attribute.pk]))
    assert response.status_code == 200


def test_staff_cant_view_products_attribute_details(
        staff_client, color_attribute):
    response = staff_client.get(reverse('dashboard:product-attribute-details',
                                        args=[color_attribute.pk]))
    assert response.status_code == 302


def test_admin_can_view_products_attribute_update(
        admin_client, color_attribute):
    response = admin_client.get(reverse('dashboard:product-attribute-update',
                                        args=[color_attribute.pk]))
    assert response.status_code == 200


def test_staff_cant_view_products_attribute_update(
        staff_client, color_attribute):
    response = staff_client.get(reverse('dashboard:product-attribute-update',
                                        args=[color_attribute.pk]))
    assert response.status_code == 302


def test_admin_can_view_products_attribute_delete(
        admin_client, color_attribute):
    response = admin_client.get(reverse('dashboard:product-attribute-delete',
                                        args=[color_attribute.pk]))
    assert response.status_code == 200


def test_staff_cant_view_products_attribute_delete(
        staff_client, color_attribute):
    response = staff_client.get(reverse('dashboard:product-attribute-delete',
                                        args=[color_attribute.pk]))
    assert response.status_code == 302


def test_admin_can_view_shipping_methods_list(admin_client):
    response = admin_client.get(reverse('dashboard:shipping-methods'))
    assert response.status_code == 200


def test_staff_cant_view_shipping_methods_list(staff_client):
    response = staff_client.get(reverse('dashboard:shipping-methods'))
    assert response.status_code == 302


def test_admin_can_view_shipping_methods_add(admin_client):
    response = admin_client.get(reverse('dashboard:shipping-method-add'))
    assert response.status_code == 200


def test_staff_cant_view_shipping_methods_add(staff_client):
    response = staff_client.get(reverse('dashboard:shipping-method-add'))
    assert response.status_code == 302


def test_admin_can_view_shipping_methods_update(admin_client, shipping_method):
    response = admin_client.get(reverse('dashboard:shipping-method-update',
                                        args=[shipping_method.pk]))
    assert response.status_code == 200


def test_staff_cant_view_shipping_methods_update(
        staff_client, shipping_method):
    response = staff_client.get(reverse('dashboard:shipping-method-update',
                                        args=[shipping_method.pk]))
    assert response.status_code == 302


def test_admin_can_view_shipping_methods_details(admin_client, shipping_method):
    response = admin_client.get(reverse('dashboard:shipping-method-details',
                                        args=[shipping_method.pk]))
    assert response.status_code == 200


def test_staff_cant_view_shipping_methods_details(
        staff_client, shipping_method):
    response = staff_client.get(reverse('dashboard:shipping-method-details',
                                        args=[shipping_method.pk]))
    assert response.status_code == 302


def test_admin_can_view_shipping_methods_delete(admin_client, shipping_method):
    response = admin_client.get(reverse('dashboard:shipping-method-delete',
                                        args=[shipping_method.pk]))
    assert response.status_code == 200


def test_staff_cant_view_shipping_methods_delete(
        staff_client, shipping_method):
    response = staff_client.get(reverse('dashboard:shipping-method-delete',
                                        args=[shipping_method.pk]))
    assert response.status_code == 302


def test_admin_can_view_customers_list(admin_client):
    response = admin_client.get(reverse('dashboard:customers'))
    assert response.status_code == 200


def test_admin_can_view_customer_detail_view(admin_client, customer_user):
    response = admin_client.get(reverse('dashboard:customer-details',
                                        args=[customer_user.pk]))
    assert response.status_code == 200


def test_admin_can_view_customer_create(admin_client):
    response = admin_client.get(reverse('dashboard:customer-create'))
    assert response.status_code == 200


def test_staff_cant_view_customer_create(staff_client):
    response = staff_client.get(reverse('dashboard:customer-create'))
    assert response.status_code == 302


def test_staff_cant_access_product_list(staff_client, staff_user):
    assert not staff_user.has_perm('product.view_product')
    response = staff_client.get(reverse('dashboard:product-list'))
    assert response.status_code == 302


def test_staff_can_access_product_list(
        staff_client, staff_user, permission_view_product):
    assert not staff_user.has_perm('product.view_product')
    staff_user.user_permissions.add(permission_view_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.view_product')
    response = staff_client.get(reverse('dashboard:product-list'))
    assert response.status_code == 200


def test_staff_can_access_product_details(
        staff_client, staff_user, permission_view_product, product):
    assert not staff_user.has_perm('product.view_product')
    url = reverse('dashboard:product-details', kwargs={'pk': product.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_view_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.view_product')

    response = staff_client.post(url)
    assert response.status_code == 200


def test_staff_can_access_product_toggle_is_published(
        staff_client, staff_user, permission_edit_product, product):
    assert not staff_user.has_perm('product.edit_product')
    url = reverse('dashboard:product-publish', kwargs={'pk': product.pk})

    response = staff_client.post(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_product')

    response = staff_client.post(url)
    assert response.status_code == 200


def test_staff_can_access_product_select_type(
        staff_client, staff_user, permission_edit_product):
    assert not staff_user.has_perm('product.edit_product')
    url = reverse('dashboard:product-add-select-type')

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_product')

    response = staff_client.post(url)
    assert response.status_code == 200


def test_staff_can_access_product_create(
        staff_client, staff_user, permission_edit_product, product_type):
    assert not staff_user.has_perm('product.edit_product')
    url = reverse('dashboard:product-add', kwargs={'type_pk': product_type.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_product')

    response = staff_client.post(url)
    assert response.status_code == 200


def test_staff_can_access_product_edit(
        staff_client, staff_user, permission_edit_product, product):
    assert not staff_user.has_perm('product.edit_product')
    url = reverse('dashboard:product-update', kwargs={'pk': product.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_product')

    response = staff_client.post(url)
    assert response.status_code == 200


def test_staff_can_access_product_delete(
        staff_client, staff_user, permission_edit_product, product):
    assert not staff_user.has_perm('product.edit_product')
    url = reverse('dashboard:product-delete', kwargs={'pk': product.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_product')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_group_member_can_view_product_list(
        staff_client, staff_user, staff_group, permission_view_product):
    assert not staff_user.has_perm('product.view_product')
    response = staff_client.get(reverse('dashboard:product-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_product)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.view_product')
    response = staff_client.get(reverse('dashboard:product-list'))
    assert response.status_code == 200


def test_staff_group_member_can_view_category_list(
        staff_client, staff_user, staff_group, permission_view_category):
    assert not staff_user.has_perm('product.view_category')
    response = staff_client.get(reverse('dashboard:category-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_category)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.view_category')
    response = staff_client.get(reverse('dashboard:category-list'))
    assert response.status_code == 200


def test_staff_group_member_can_view_category_add_root(
        staff_client, staff_user, staff_group, permission_edit_category):
    assert not staff_user.has_perm('product.edit_category')
    response = staff_client.get(reverse('dashboard:category-add'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_category)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_category')
    response = staff_client.get(reverse('dashboard:category-add'))
    assert response.status_code == 200


def test_staff_group_member_can_view_category_add_subcategory(
        staff_client, staff_user, staff_group, permission_edit_category,
        default_category):
    assert not staff_user.has_perm('product.edit_category')
    response = staff_client.get(reverse('dashboard:category-add',
                                        args=[default_category.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_category)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_category')
    response = staff_client.get(reverse('dashboard:category-add',
                                        args=[default_category.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_category_edit(
        staff_client, staff_user, staff_group, permission_edit_category,
        default_category):
    assert not staff_user.has_perm('product.edit_category')
    response = staff_client.get(reverse('dashboard:category-edit',
                                        args=[default_category.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_category)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_category')
    response = staff_client.get(reverse('dashboard:category-edit',
                                        args=[default_category.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_category_delete(
        staff_client, staff_user, staff_group, permission_edit_category,
        default_category):
    assert not staff_user.has_perm('product.edit_category')
    response = staff_client.get(reverse('dashboard:category-delete',
                                        args=[default_category.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_category)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_category')
    response = staff_client.get(reverse('dashboard:category-delete',
                                        args=[default_category.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_sale_list(
        staff_client, staff_user, staff_group, permission_view_sale):
    assert not staff_user.has_perm('discount.view_sale')
    response = staff_client.get(reverse('dashboard:sale-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_sale)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('discount.view_sale')
    response = staff_client.get(reverse('dashboard:sale-list'))
    assert response.status_code == 200


def test_staff_group_member_can_view_sale_update(
        staff_client, staff_user, staff_group, permission_edit_sale, sale):
    assert not staff_user.has_perm('discount.edit_sale')
    response = staff_client.get(reverse('dashboard:sale-update',
                                        args=[sale.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_sale)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('discount.edit_sale')
    response = staff_client.get(reverse('dashboard:sale-update',
                                        args=[sale.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_sale_add(
        staff_client, staff_user, staff_group, permission_edit_sale, sale):
    assert not staff_user.has_perm('discount.edit_sale')
    response = staff_client.get(reverse('dashboard:sale-add'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_sale)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('discount.edit_sale')
    response = staff_client.get(reverse('dashboard:sale-add'))
    assert response.status_code == 200


def test_staff_group_member_can_view_sale_delete(
        staff_client, staff_user, staff_group, permission_edit_sale, sale):
    assert not staff_user.has_perm('discount.edit_sale')
    response = staff_client.get(reverse('dashboard:sale-delete',
                                        args=[sale.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_sale)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('discount.edit_sale')
    response = staff_client.get(reverse('dashboard:sale-delete',
                                        args=[sale.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_voucher_list(
        staff_client, staff_user, staff_group, permission_view_voucher):
    assert not staff_user.has_perm('discount.view_voucher')
    response = staff_client.get(reverse('dashboard:voucher-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_voucher)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('discount.view_voucher')
    response = staff_client.get(reverse('dashboard:voucher-list'))
    assert response.status_code == 200


def test_staff_group_member_can_view_voucher_update(
        staff_client, staff_user, staff_group, permission_edit_voucher,
        voucher):
    assert not staff_user.has_perm('discount.edit_voucher')
    response = staff_client.get(reverse('dashboard:voucher-update',
                                        args=[voucher.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_voucher)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('discount.edit_voucher')
    response = staff_client.get(reverse('dashboard:voucher-update',
                                        args=[voucher.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_voucher_add(
        staff_client, staff_user, staff_group, permission_edit_voucher):
    assert not staff_user.has_perm('discount.edit_voucher')
    response = staff_client.get(reverse('dashboard:voucher-add'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_voucher)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('discount.edit_voucher')
    response = staff_client.get(reverse('dashboard:voucher-add'))
    assert response.status_code == 200


def test_staff_group_member_can_view_voucher_delete(
        staff_client, staff_user, staff_group, permission_edit_voucher,
        voucher):
    assert not staff_user.has_perm('discount.edit_voucher')
    response = staff_client.get(reverse('dashboard:voucher-delete',
                                        args=[voucher.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_voucher)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('discount.edit_voucher')
    response = staff_client.get(reverse('dashboard:voucher-delete',
                                        args=[voucher.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_order_list(
        staff_client, staff_user, staff_group, permission_view_order):
    assert not staff_user.has_perm('order.view_order')
    response = staff_client.get(reverse('dashboard:orders'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_order)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('order.view_order')
    response = staff_client.get(reverse('dashboard:orders'))
    assert response.status_code == 200


def test_staff_group_member_can_view_order_details(
        staff_client, staff_user, staff_group, permission_view_order,
        order_with_lines):
    assert not staff_user.has_perm('order.view_order')
    response = staff_client.get(reverse('dashboard:order-details',
                                        args=[order_with_lines.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_order)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('order.view_order')
    response = staff_client.get(reverse('dashboard:order-details',
                                        args=[order_with_lines.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_order_add_note(
        staff_client, staff_user, staff_group, permission_edit_order, order):
    assert not staff_user.has_perm('order.edit_order')
    response = staff_client.get(reverse('dashboard:order-add-note',
                                        args=[order.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_order)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('order.edit_order')
    response = staff_client.get(reverse('dashboard:order-add-note',
                                        args=[order.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_cancel_order(
        staff_client, staff_user, staff_group, permission_edit_order,
        order):
    assert not staff_user.has_perm('order.edit_order')
    response = staff_client.get(
        reverse('dashboard:order-cancel', args=[order.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_order)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('order.edit_order')
    response = staff_client.get(
        reverse('dashboard:order-cancel', args=[order.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_billing_address_edit(
        staff_client, staff_user, staff_group, permission_edit_order,
        order):
    assert not staff_user.has_perm('order.edit_order')
    response = staff_client.get(reverse('dashboard:address-edit',
                                        args=[order.pk, 'billing']))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_order)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('order.edit_order')
    response = staff_client.get(reverse('dashboard:address-edit',
                                        args=[order.pk, 'billing']))
    assert response.status_code == 200


def test_staff_group_member_can_view_customers_list(
        staff_client, staff_user, staff_group, permission_view_user):
    assert not staff_user.has_perm('account.view_user')
    response = staff_client.get(reverse('dashboard:customers'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_user)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('account.view_user')
    response = staff_client.get(reverse('dashboard:customers'))
    assert response.status_code == 200


def test_staff_group_member_can_view_customer_details(
        staff_client, staff_user, staff_group, permission_view_user,
        customer_user, order_with_lines):
    assert not staff_user.has_perm('account.view_user')
    response = staff_client.get(reverse('dashboard:customer-details',
                                        args=[customer_user.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_user)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('account.view_user')
    response = staff_client.get(reverse('dashboard:customer-details',
                                        args=[customer_user.pk]))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:order-details',
                                        args=[order_with_lines.pk]))
    assert response.status_code == 302


def test_staff_group_member_can_view_staff_members_list(
        staff_client, staff_user, staff_group, permission_view_staff):
    assert not staff_user.has_perm('account.view_staff')
    response = staff_client.get(reverse('dashboard:staff-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_staff)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('account.view_staff')
    response = staff_client.get(reverse('dashboard:staff-list'))
    assert response.status_code == 200


def test_staff_group_member_can_view_detail_create_and_delete_staff_members(
        staff_client, staff_user, staff_group, permission_edit_staff):
    assert not staff_user.has_perm('account.edit_staff')
    response = staff_client.get(reverse('dashboard:staff-create'))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:staff-delete',
                                        args=[staff_user.pk]))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:staff-details',
                                        args=[staff_user.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_staff)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('account.edit_staff')
    response = staff_client.get(reverse('dashboard:staff-create'))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:staff-delete',
                                        args=[staff_user.pk]))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:staff-details',
                                        args=[staff_user.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_group_list_and_details(
        staff_client, staff_user, staff_group, permission_view_group):
    assert not staff_user.has_perm('account.view_group')
    response = staff_client.get(reverse('dashboard:group-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_group)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('account.view_group')
    response = staff_client.get(reverse('dashboard:group-list'))
    assert response.status_code == 200


def test_staff_with_permission_can_create_and_delete_group(
        staff_client, staff_user, staff_group, permission_edit_group):
    assert not staff_user.has_perm('account.edit_group')
    response = staff_client.get(reverse('dashboard:group-delete',
                                        args=[staff_group.pk]))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:group-details',
                                        args=[staff_group.pk]))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:group-create'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_group)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('account.edit_group')
    response = staff_client.get(reverse('dashboard:group-details',
                                        args=[staff_group.pk]))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:group-delete',
                                        args=[staff_group.pk]))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:group-create'))
    assert response.status_code == 200


def test_staff_with_permissions_can_view_product_types_list(
        staff_client, staff_user, staff_group, permission_view_properties):
    assert not staff_user.has_perm('product.view_properties')
    response = staff_client.get(reverse('dashboard:product-type-list'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_properties)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.view_properties')
    response = staff_client.get(reverse('dashboard:product-type-list'))
    assert response.status_code == 200


def test_staff_with_permissions_can_edit_add_and_delete_product_types_list(
        staff_client, staff_user, staff_group, permission_edit_properties,
        product_type):
    assert not staff_user.has_perm('product.edit_properties')
    response = staff_client.get(reverse('dashboard:product-type-update',
                                        args=[product_type.pk]))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:product-type-delete',
                                        args=[product_type.pk]))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:product-type-add'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_properties)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_properties')
    response = staff_client.get(reverse('dashboard:product-type-update',
                                        args=[product_type.pk]))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:product-type-delete',
                                        args=[product_type.pk]))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:product-type-add'))
    assert response.status_code == 200


def test_staff_can_access_variant_details(
        staff_client, staff_user, permission_view_product, product):
    product_type = product.product_type
    product_type.has_variants = True
    product_type.save()

    variant = product.variants.get()
    assert not staff_user.has_perm('product.view_product')
    url = reverse(
        'dashboard:variant-details',
        kwargs={'product_pk': product.pk, 'variant_pk': variant.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_view_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.view_product')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_can_access_variant_create(
        staff_client, staff_user, permission_edit_product, product):
    assert not staff_user.has_perm('product.edit_product')
    url = reverse('dashboard:variant-add', kwargs={'product_pk': product.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_product')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_can_access_variant_edit(
        staff_client, staff_user, permission_edit_product, product):
    variant = product.variants.get()
    assert not staff_user.has_perm('product.edit_product')
    url = reverse(
        'dashboard:variant-update',
        kwargs={'product_pk': product.pk, 'variant_pk': variant.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_product')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_can_access_variant_delete(
        staff_client, staff_user, permission_edit_product, product):
    variant = product.variants.get()
    assert not staff_user.has_perm('product.edit_product')
    url = reverse(
        'dashboard:variant-delete',
        kwargs={'product_pk': product.pk, 'variant_pk': variant.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_product')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_can_access_variant_images(
        staff_client, staff_user, permission_view_product, product):
    variant = product.variants.get()
    assert not staff_user.has_perm('product.view_product')
    url = reverse(
        'dashboard:variant-images',
        kwargs={'product_pk': product.pk, 'variant_pk': variant.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_view_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.view_product')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_can_access_product_image_list(
        staff_client, staff_user, permission_view_product, product):
    assert not staff_user.has_perm('product.view_product')
    url = reverse(
        'dashboard:product-image-list', kwargs={'product_pk': product.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_view_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.view_product')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_can_access_product_image_add(
        staff_client, staff_user, permission_edit_product, product):
    assert not staff_user.has_perm('product.edit_product')
    url = reverse(
        'dashboard:product-image-add', kwargs={'product_pk': product.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_product')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_can_access_product_image_update(
        staff_client, staff_user, permission_edit_product, product_with_image):
    product_image = product_with_image.images.get()
    assert not staff_user.has_perm('product.edit_product')
    url = reverse(
        'dashboard:product-image-update',
        kwargs={
            'product_pk': product_with_image.pk,
            'img_pk': product_image.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_product')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_can_access_product_image_delete(
        staff_client, staff_user, permission_edit_product, product_with_image):
    product_image = product_with_image.images.get()
    assert not staff_user.has_perm('product.edit_product')
    url = reverse(
        'dashboard:product-image-delete',
        kwargs={
            'product_pk': product_with_image.pk,
            'img_pk': product_image.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_product)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_product')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_with_permissions_can_view_products_attributes_list(
        staff_client, staff_user, staff_group, permission_view_properties,
        color_attribute):
    assert not staff_user.has_perm('product.view_properties')
    response = staff_client.get(reverse('dashboard:product-attributes'))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:product-attribute-details',
                                        args=[color_attribute.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_properties)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.view_properties')
    response = staff_client.get(reverse('dashboard:product-attributes'))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:product-attribute-details',
                                        args=[color_attribute.pk]))
    assert response.status_code == 200


def test_staff_with_permissions_can_update_add_and_delete_products_attributes(
        staff_client, staff_user, staff_group, permission_edit_properties,
        color_attribute):
    assert not staff_user.has_perm('product.edit_properties')
    response = staff_client.get(reverse('dashboard:product-attribute-update',
                                        args=[color_attribute.pk]))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:product-attribute-delete',
                                        args=[color_attribute.pk]))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:product-attribute-add'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_properties)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_properties')
    response = staff_client.get(reverse('dashboard:product-attribute-update',
                                        args=[color_attribute.pk]))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:product-attribute-delete',
                                        args=[color_attribute.pk]))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:product-attribute-add'))
    assert response.status_code == 200


def test_staff_can_access_attribute_create(
        staff_client, staff_user, permission_edit_properties, color_attribute):
    assert not staff_user.has_perm('product.edit_properties')
    url = reverse(
        'dashboard:product-attribute-value-add',
        kwargs={'attribute_pk': color_attribute.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_properties)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_properties')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_can_access_attribute_edit(
        staff_client, staff_user, permission_edit_properties, color_attribute):
    value = color_attribute.values.first()
    assert not staff_user.has_perm('product.edit_properties')
    url = reverse(
        'dashboard:product-attribute-value-update',
        kwargs={
            'attribute_pk': color_attribute.pk,
            'value_pk': value.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_properties)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_properties')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_can_access_attribute_delete(
        staff_client, staff_user, permission_edit_properties, color_attribute):
    value = color_attribute.values.first()
    assert not staff_user.has_perm('product.edit_properties')
    url = reverse(
        'dashboard:product-attribute-value-delete',
        kwargs={
            'attribute_pk': color_attribute.pk,
            'value_pk': value.pk})

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_user.user_permissions.add(permission_edit_properties)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('product.edit_properties')

    response = staff_client.get(url)
    assert response.status_code == 200


def test_staff_with_permissions_can_view_shipping_methods_and_details(
        staff_client, staff_user, staff_group, permission_view_shipping,
        shipping_method):
    assert not staff_user.has_perm('shipping.view_shipping')
    response = staff_client.get(reverse('dashboard:shipping-methods'))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:shipping-method-details',
                                        args=[shipping_method.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_view_shipping)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('shipping.view_shipping')
    response = staff_client.get(reverse('dashboard:shipping-methods'))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:shipping-method-details',
                                        args=[shipping_method.pk]))
    assert response.status_code == 200


def test_staff_with_permissions_can_update_add_and_delete_shipping_method(
        staff_client, staff_user, staff_group, permission_edit_shipping,
        shipping_method):
    assert not staff_user.has_perm('shipping.edit_shipping')
    response = staff_client.get(reverse('dashboard:shipping-method-update',
                                        args=[shipping_method.pk]))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:shipping-method-delete',
                                        args=[shipping_method.pk]))
    assert response.status_code == 302
    response = staff_client.get(reverse('dashboard:shipping-method-add'))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_shipping)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('shipping.edit_shipping')
    response = staff_client.get(reverse('dashboard:shipping-method-update',
                                        args=[shipping_method.pk]))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:shipping-method-delete',
                                        args=[shipping_method.pk]))
    assert response.status_code == 200
    response = staff_client.get(reverse('dashboard:shipping-method-add'))
    assert response.status_code == 200


def test_staff_with_permissions_can_edit_customer(
        staff_client, customer_user, staff_user, staff_group,
        permission_edit_user, permission_view_user):
    assert customer_user.email == 'test@example.com'
    response = staff_client.get(reverse('dashboard:customer-update',
                                        args=[customer_user.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_user)
    staff_group.permissions.add(permission_view_user)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('account.edit_user')
    assert staff_user.has_perm('account.view_user')
    response = staff_client.get(reverse('dashboard:customer-update',
                                        args=[customer_user.pk]))
    assert response.status_code == 200
    url = reverse('dashboard:customer-update', args=[customer_user.pk])
    data = {'email': 'newemail@example.com', 'is_active': True}
    staff_client.post(url, data)
    customer_user = User.objects.get(pk=customer_user.pk)
    assert customer_user.email == 'newemail@example.com'
    assert customer_user.is_active


def test_staff_with_permissions_can_add_customer(
        staff_client, staff_user, staff_group, permission_edit_user,
        permission_view_user):
    staff_group.permissions.add(permission_edit_user)
    staff_group.permissions.add(permission_view_user)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('account.edit_user')
    assert staff_user.has_perm('account.view_user')
    response = staff_client.get(reverse('dashboard:customer-create'))
    assert response.status_code == 200
    url = reverse('dashboard:customer-create')
    data = {'email': 'newcustomer@example.com', 'is_active': True}
    staff_client.post(url, data)
    customer = User.objects.get(email='newcustomer@example.com')
    assert customer.is_active


def test_staff_group_member_can_view_and_edit_site_settings(
        staff_client, staff_user, staff_group, site_settings,
        permission_edit_settings):
    assert not staff_user.has_perm('site.edit_settings')
    response = staff_client.get(reverse('dashboard:site-update',
                                        args=[site_settings.pk]))
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_settings)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('site.edit_settings')
    response = staff_client.get(reverse('dashboard:site-update',
                                        args=[site_settings.pk]))
    assert response.status_code == 200


def test_staff_group_member_can_view_and_edit_taxes_settings(
        staff_client, staff_user, staff_group, site_settings,
        permission_edit_settings):
    assert not staff_user.has_perm('site.edit_settings')
    url = reverse('dashboard:configure-taxes')
    response = staff_client.get(url)
    assert response.status_code == 302
    staff_group.permissions.add(permission_edit_settings)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('site.edit_settings')
    response = staff_client.get(url)


def test_staff_group_member_can_view_menus_and_details(
        staff_client, staff_user, staff_group, permission_view_menu,
        menu_item):
    menu_list_url = reverse('dashboard:menu-list')
    menu_details_url = reverse(
        'dashboard:menu-details', args=[menu_item.menu.pk])
    menu_item_details_url = reverse(
        'dashboard:menu-item-details', args=[menu_item.menu.pk, menu_item.pk])

    assert not staff_user.has_perm('menu.view_menu')
    response = staff_client.get(menu_list_url)
    assert response.status_code == 302
    response = staff_client.get(menu_details_url)
    assert response.status_code == 302
    response = staff_client.get(menu_item_details_url)
    assert response.status_code == 302

    staff_group.permissions.add(permission_view_menu)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('menu.view_menu')

    response = staff_client.get(menu_list_url)
    assert response.status_code == 200
    response = staff_client.get(menu_details_url)
    assert response.status_code == 200
    response = staff_client.get(menu_item_details_url)
    assert response.status_code == 200


def test_staff_group_member_can_edit_menus(
        staff_client, staff_user, staff_group, permission_edit_menu,
        menu_item):
    menu_add_url = reverse('dashboard:menu-add')
    menu_edit_url = reverse('dashboard:menu-edit', args=[menu_item.menu.pk])
    menu_delete_url = reverse(
        'dashboard:menu-delete', args=[menu_item.menu.pk])

    assert not staff_user.has_perm('menu.view_menu')
    response = staff_client.get(menu_add_url)
    assert response.status_code == 302
    response = staff_client.get(menu_edit_url)
    assert response.status_code == 302
    response = staff_client.get(menu_delete_url)
    assert response.status_code == 302

    staff_group.permissions.add(permission_edit_menu)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('menu.edit_menu')

    response = staff_client.get(menu_add_url)
    assert response.status_code == 200
    response = staff_client.get(menu_edit_url)
    assert response.status_code == 200
    response = staff_client.get(menu_delete_url)
    assert response.status_code == 200


def test_staff_group_member_can_edit_menu_items(
        staff_client, staff_user, staff_group, permission_edit_menu,
        menu_item):
    menu_item_add_url = reverse(
        'dashboard:menu-item-add', args=[menu_item.menu.pk, menu_item.pk])
    menu_item_edit_url = reverse(
        'dashboard:menu-item-edit', args=[menu_item.menu.pk, menu_item.pk])
    menu_item_delete_url = reverse(
        'dashboard:menu-item-delete', args=[menu_item.menu.pk, menu_item.pk])

    assert not staff_user.has_perm('menu.view_menu')
    response = staff_client.get(menu_item_add_url)
    assert response.status_code == 302
    response = staff_client.get(menu_item_edit_url)
    assert response.status_code == 302
    response = staff_client.get(menu_item_delete_url)
    assert response.status_code == 302

    staff_group.permissions.add(permission_edit_menu)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)
    assert staff_user.has_perm('menu.edit_menu')

    response = staff_client.get(menu_item_add_url)
    assert response.status_code == 200
    response = staff_client.get(menu_item_edit_url)
    assert response.status_code == 200
    response = staff_client.get(menu_item_delete_url)
    assert response.status_code == 200


def test_staff_group_member_can_remove_user(
        staff_client, staff_user, staff_group, permission_edit_user):
    url = reverse('dashboard:customer-delete', args=[staff_user.pk])

    response = staff_client.get(url)
    assert response.status_code == 302

    staff_group.permissions.add(permission_edit_user)
    staff_user.groups.add(staff_group)
    staff_user = User.objects.get(pk=staff_user.pk)

    response = staff_client.get(url)
    assert response.status_code == 200
