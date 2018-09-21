import { StaffList_staffUsers_edges_node } from "./types/StaffList";
import { StaffMemberDetails_user } from "./types/StaffMemberDetails";

export const staffMembers: StaffList_staffUsers_edges_node[] = [
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: false
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: false
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: false
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: false
  },
  {
    email: "admin@example.com",
    id: "VXNlcjoyMQ==",
    isActive: true
  }
].map(staffMember => ({ __typename: "User" as "User", ...staffMember }));
export const staffMember: StaffMemberDetails_user = {
  __typename: "User",
  email: "admin@example.com",
  id: "VXNlcjoyMQ==",
  isActive: true,
  permissions: [
    {
      code: "account.add_address",
      name: "Can add address"
    },
    {
      code: "account.change_address",
      name: "Can change address"
    },
    {
      code: "account.delete_address",
      name: "Can delete address"
    },
    {
      code: "account.add_customernote",
      name: "Can add customer note"
    },
    {
      code: "account.change_customernote",
      name: "Can change customer note"
    },
    {
      code: "account.delete_customernote",
      name: "Can delete customer note"
    },
    {
      code: "account.add_user",
      name: "Can add user"
    },
    {
      code: "account.change_user",
      name: "Can change user"
    },
    {
      code: "account.delete_user",
      name: "Can delete user"
    },
    {
      code: "account.impersonate_users",
      name: "Impersonate customers."
    },
    {
      code: "account.manage_staff",
      name: "Manage staff."
    },
    {
      code: "account.manage_users",
      name: "Manage customers."
    },
    {
      code: "auth.add_group",
      name: "Can add group"
    },
    {
      code: "auth.change_group",
      name: "Can change group"
    },
    {
      code: "auth.delete_group",
      name: "Can delete group"
    },
    {
      code: "auth.add_permission",
      name: "Can add permission"
    },
    {
      code: "auth.change_permission",
      name: "Can change permission"
    },
    {
      code: "auth.delete_permission",
      name: "Can delete permission"
    },
    {
      code: "checkout.add_cart",
      name: "Can add cart"
    },
    {
      code: "checkout.change_cart",
      name: "Can change cart"
    },
    {
      code: "checkout.delete_cart",
      name: "Can delete cart"
    },
    {
      code: "checkout.add_cartline",
      name: "Can add cart line"
    },
    {
      code: "checkout.change_cartline",
      name: "Can change cart line"
    },
    {
      code: "checkout.delete_cartline",
      name: "Can delete cart line"
    },
    {
      code: "contenttypes.add_contenttype",
      name: "Can add content type"
    },
    {
      code: "contenttypes.change_contenttype",
      name: "Can change content type"
    },
    {
      code: "contenttypes.delete_contenttype",
      name: "Can delete content type"
    },
    {
      code: "discount.add_sale",
      name: "Can add sale"
    },
    {
      code: "discount.change_sale",
      name: "Can change sale"
    },
    {
      code: "discount.delete_sale",
      name: "Can delete sale"
    },
    {
      code: "discount.manage_discounts",
      name: "Manage sales and vouchers."
    },
    {
      code: "discount.add_voucher",
      name: "Can add voucher"
    },
    {
      code: "discount.change_voucher",
      name: "Can change voucher"
    },
    {
      code: "discount.delete_voucher",
      name: "Can delete voucher"
    },
    {
      code: "discount.add_vouchertranslation",
      name: "Can add voucher translation"
    },
    {
      code: "discount.change_vouchertranslation",
      name: "Can change voucher translation"
    },
    {
      code: "discount.delete_vouchertranslation",
      name: "Can delete voucher translation"
    },
    {
      code: "django_celery_results.add_taskresult",
      name: "Can add task result"
    },
    {
      code: "django_celery_results.change_taskresult",
      name: "Can change task result"
    },
    {
      code: "django_celery_results.delete_taskresult",
      name: "Can delete task result"
    },
    {
      code: "django_prices_openexchangerates.add_conversionrate",
      name: "Can add conversion rate"
    },
    {
      code: "django_prices_openexchangerates.change_conversionrate",
      name: "Can change conversion rate"
    },
    {
      code: "django_prices_openexchangerates.delete_conversionrate",
      name: "Can delete conversion rate"
    },
    {
      code: "django_prices_vatlayer.add_ratetypes",
      name: "Can add rate types"
    },
    {
      code: "django_prices_vatlayer.change_ratetypes",
      name: "Can change rate types"
    },
    {
      code: "django_prices_vatlayer.delete_ratetypes",
      name: "Can delete rate types"
    },
    {
      code: "django_prices_vatlayer.add_vat",
      name: "Can add vat"
    },
    {
      code: "django_prices_vatlayer.change_vat",
      name: "Can change vat"
    },
    {
      code: "django_prices_vatlayer.delete_vat",
      name: "Can delete vat"
    },
    {
      code: "impersonate.add_impersonationlog",
      name: "Can add impersonation log"
    },
    {
      code: "impersonate.change_impersonationlog",
      name: "Can change impersonation log"
    },
    {
      code: "impersonate.delete_impersonationlog",
      name: "Can delete impersonation log"
    },
    {
      code: "menu.add_menu",
      name: "Can add menu"
    },
    {
      code: "menu.change_menu",
      name: "Can change menu"
    },
    {
      code: "menu.delete_menu",
      name: "Can delete menu"
    },
    {
      code: "menu.manage_menus",
      name: "Manage navigation."
    },
    {
      code: "menu.add_menuitem",
      name: "Can add menu item"
    },
    {
      code: "menu.change_menuitem",
      name: "Can change menu item"
    },
    {
      code: "menu.delete_menuitem",
      name: "Can delete menu item"
    },
    {
      code: "menu.add_menuitemtranslation",
      name: "Can add menu item translation"
    },
    {
      code: "menu.change_menuitemtranslation",
      name: "Can change menu item translation"
    },
    {
      code: "menu.delete_menuitemtranslation",
      name: "Can delete menu item translation"
    },
    {
      code: "order.add_fulfillment",
      name: "Can add fulfillment"
    },
    {
      code: "order.change_fulfillment",
      name: "Can change fulfillment"
    },
    {
      code: "order.delete_fulfillment",
      name: "Can delete fulfillment"
    },
    {
      code: "order.add_fulfillmentline",
      name: "Can add fulfillment line"
    },
    {
      code: "order.change_fulfillmentline",
      name: "Can change fulfillment line"
    },
    {
      code: "order.delete_fulfillmentline",
      name: "Can delete fulfillment line"
    },
    {
      code: "order.add_order",
      name: "Can add order"
    },
    {
      code: "order.change_order",
      name: "Can change order"
    },
    {
      code: "order.delete_order",
      name: "Can delete order"
    },
    {
      code: "order.manage_orders",
      name: "Manage orders."
    },
    {
      code: "order.add_orderevent",
      name: "Can add order event"
    },
    {
      code: "order.change_orderevent",
      name: "Can change order event"
    },
    {
      code: "order.delete_orderevent",
      name: "Can delete order event"
    },
    {
      code: "order.add_orderhistoryentry",
      name: "Can add order history entry"
    },
    {
      code: "order.change_orderhistoryentry",
      name: "Can change order history entry"
    },
    {
      code: "order.delete_orderhistoryentry",
      name: "Can delete order history entry"
    },
    {
      code: "order.add_orderline",
      name: "Can add order line"
    },
    {
      code: "order.change_orderline",
      name: "Can change order line"
    },
    {
      code: "order.delete_orderline",
      name: "Can delete order line"
    },
    {
      code: "order.add_ordernote",
      name: "Can add order note"
    },
    {
      code: "order.change_ordernote",
      name: "Can change order note"
    },
    {
      code: "order.delete_ordernote",
      name: "Can delete order note"
    },
    {
      code: "order.add_payment",
      name: "Can add payment"
    },
    {
      code: "order.change_payment",
      name: "Can change payment"
    },
    {
      code: "order.delete_payment",
      name: "Can delete payment"
    },
    {
      code: "page.add_page",
      name: "Can add page"
    },
    {
      code: "page.change_page",
      name: "Can change page"
    },
    {
      code: "page.delete_page",
      name: "Can delete page"
    },
    {
      code: "page.manage_pages",
      name: "Manage pages."
    },
    {
      code: "page.add_pagetranslation",
      name: "Can add page translation"
    },
    {
      code: "page.change_pagetranslation",
      name: "Can change page translation"
    },
    {
      code: "page.delete_pagetranslation",
      name: "Can delete page translation"
    },
    {
      code: "product.add_attributechoicevalue",
      name: "Can add attribute choice value"
    },
    {
      code: "product.change_attributechoicevalue",
      name: "Can change attribute choice value"
    },
    {
      code: "product.delete_attributechoicevalue",
      name: "Can delete attribute choice value"
    },
    {
      code: "product.add_attributechoicevaluetranslation",
      name: "Can add attribute choice value translation"
    },
    {
      code: "product.change_attributechoicevaluetranslation",
      name: "Can change attribute choice value translation"
    },
    {
      code: "product.delete_attributechoicevaluetranslation",
      name: "Can delete attribute choice value translation"
    },
    {
      code: "product.add_category",
      name: "Can add category"
    },
    {
      code: "product.change_category",
      name: "Can change category"
    },
    {
      code: "product.delete_category",
      name: "Can delete category"
    },
    {
      code: "product.add_categorytranslation",
      name: "Can add category translation"
    },
    {
      code: "product.change_categorytranslation",
      name: "Can change category translation"
    },
    {
      code: "product.delete_categorytranslation",
      name: "Can delete category translation"
    },
    {
      code: "product.add_collection",
      name: "Can add collection"
    },
    {
      code: "product.change_collection",
      name: "Can change collection"
    },
    {
      code: "product.delete_collection",
      name: "Can delete collection"
    },
    {
      code: "product.add_collectiontranslation",
      name: "Can add collection translation"
    },
    {
      code: "product.change_collectiontranslation",
      name: "Can change collection translation"
    },
    {
      code: "product.delete_collectiontranslation",
      name: "Can delete collection translation"
    },
    {
      code: "product.add_product",
      name: "Can add product"
    },
    {
      code: "product.change_product",
      name: "Can change product"
    },
    {
      code: "product.delete_product",
      name: "Can delete product"
    },
    {
      code: "product.manage_products",
      name: "Manage products."
    },
    {
      code: "product.add_productattribute",
      name: "Can add product attribute"
    },
    {
      code: "product.change_productattribute",
      name: "Can change product attribute"
    },
    {
      code: "product.delete_productattribute",
      name: "Can delete product attribute"
    },
    {
      code: "product.add_productattributetranslation",
      name: "Can add product attribute translation"
    },
    {
      code: "product.change_productattributetranslation",
      name: "Can change product attribute translation"
    },
    {
      code: "product.delete_productattributetranslation",
      name: "Can delete product attribute translation"
    },
    {
      code: "product.add_productimage",
      name: "Can add product image"
    },
    {
      code: "product.change_productimage",
      name: "Can change product image"
    },
    {
      code: "product.delete_productimage",
      name: "Can delete product image"
    },
    {
      code: "product.add_producttranslation",
      name: "Can add product translation"
    },
    {
      code: "product.change_producttranslation",
      name: "Can change product translation"
    },
    {
      code: "product.delete_producttranslation",
      name: "Can delete product translation"
    },
    {
      code: "product.add_producttype",
      name: "Can add product type"
    },
    {
      code: "product.change_producttype",
      name: "Can change product type"
    },
    {
      code: "product.delete_producttype",
      name: "Can delete product type"
    },
    {
      code: "product.add_productvariant",
      name: "Can add product variant"
    },
    {
      code: "product.change_productvariant",
      name: "Can change product variant"
    },
    {
      code: "product.delete_productvariant",
      name: "Can delete product variant"
    },
    {
      code: "product.add_productvarianttranslation",
      name: "Can add product variant translation"
    },
    {
      code: "product.change_productvarianttranslation",
      name: "Can change product variant translation"
    },
    {
      code: "product.delete_productvarianttranslation",
      name: "Can delete product variant translation"
    },
    {
      code: "product.add_variantimage",
      name: "Can add variant image"
    },
    {
      code: "product.change_variantimage",
      name: "Can change variant image"
    },
    {
      code: "product.delete_variantimage",
      name: "Can delete variant image"
    },
    {
      code: "sessions.add_session",
      name: "Can add session"
    },
    {
      code: "sessions.change_session",
      name: "Can change session"
    },
    {
      code: "sessions.delete_session",
      name: "Can delete session"
    },
    {
      code: "shipping.add_shippingmethod",
      name: "Can add shipping method"
    },
    {
      code: "shipping.change_shippingmethod",
      name: "Can change shipping method"
    },
    {
      code: "shipping.delete_shippingmethod",
      name: "Can delete shipping method"
    },
    {
      code: "shipping.add_shippingmethodtranslation",
      name: "Can add shipping method translation"
    },
    {
      code: "shipping.change_shippingmethodtranslation",
      name: "Can change shipping method translation"
    },
    {
      code: "shipping.delete_shippingmethodtranslation",
      name: "Can delete shipping method translation"
    },
    {
      code: "shipping.add_shippingzone",
      name: "Can add shipping zone"
    },
    {
      code: "shipping.change_shippingzone",
      name: "Can change shipping zone"
    },
    {
      code: "shipping.delete_shippingzone",
      name: "Can delete shipping zone"
    },
    {
      code: "shipping.manage_shipping",
      name: "Manage shipping."
    },
    {
      code: "site.add_authorizationkey",
      name: "Can add authorization key"
    },
    {
      code: "site.change_authorizationkey",
      name: "Can change authorization key"
    },
    {
      code: "site.delete_authorizationkey",
      name: "Can delete authorization key"
    },
    {
      code: "site.add_sitesettings",
      name: "Can add site settings"
    },
    {
      code: "site.change_sitesettings",
      name: "Can change site settings"
    },
    {
      code: "site.delete_sitesettings",
      name: "Can delete site settings"
    },
    {
      code: "site.manage_settings",
      name: "Manage settings."
    },
    {
      code: "site.add_sitesettingstranslation",
      name: "Can add site settings translation"
    },
    {
      code: "site.change_sitesettingstranslation",
      name: "Can change site settings translation"
    },
    {
      code: "site.delete_sitesettingstranslation",
      name: "Can delete site settings translation"
    },
    {
      code: "sites.add_site",
      name: "Can add site"
    },
    {
      code: "sites.change_site",
      name: "Can change site"
    },
    {
      code: "sites.delete_site",
      name: "Can delete site"
    },
    {
      code: "social_django.add_association",
      name: "Can add association"
    },
    {
      code: "social_django.change_association",
      name: "Can change association"
    },
    {
      code: "social_django.delete_association",
      name: "Can delete association"
    },
    {
      code: "social_django.add_code",
      name: "Can add code"
    },
    {
      code: "social_django.change_code",
      name: "Can change code"
    },
    {
      code: "social_django.delete_code",
      name: "Can delete code"
    },
    {
      code: "social_django.add_nonce",
      name: "Can add nonce"
    },
    {
      code: "social_django.change_nonce",
      name: "Can change nonce"
    },
    {
      code: "social_django.delete_nonce",
      name: "Can delete nonce"
    },
    {
      code: "social_django.add_partial",
      name: "Can add partial"
    },
    {
      code: "social_django.change_partial",
      name: "Can change partial"
    },
    {
      code: "social_django.delete_partial",
      name: "Can delete partial"
    },
    {
      code: "social_django.add_usersocialauth",
      name: "Can add user social auth"
    },
    {
      code: "social_django.change_usersocialauth",
      name: "Can change user social auth"
    },
    {
      code: "social_django.delete_usersocialauth",
      name: "Can delete user social auth"
    }
  ].map(perm => ({
    __typename: "PermissionDisplay" as "PermissionDisplay",
    ...perm
  }))
};
