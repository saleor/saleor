/* eslint-disable */
import { configure } from "@storybook/react";

function loadStories() {
  // Components
  require("./stories/components/ActionDialog");
  require("./stories/components/AddressEdit");
  require("./stories/components/AddressFormatter");
  require("./stories/components/CardMenu");
  require("./stories/components/DateFormatter");
  require("./stories/components/EditableTableCell");
  require("./stories/components/ErrorMessageCard");
  require("./stories/components/ExternalLink");
  require("./stories/components/Money");
  require("./stories/components/MultiAutocompleteSelectField");
  require("./stories/components/MultiSelectField");
  require("./stories/components/NotFoundPage");
  require("./stories/components/PageHeader");
  require("./stories/components/Percent");
  require("./stories/components/PhoneField");
  require("./stories/components/PriceField");
  require("./stories/components/SaveButtonBar");
  require("./stories/components/SingleAutocompleteSelectField");
  require("./stories/components/SingleSelectField");
  require("./stories/components/Skeleton");
  require("./stories/components/StatusLabel");
  require("./stories/components/TablePagination");
  require("./stories/components/Timeline");
  require("./stories/components/messages");

  // Authentication
  require("./stories/auth/LoginPage");
  require("./stories/auth/LoginLoading");

  // Categories
  require("./stories/categories/CategoryProducts");
  require("./stories/categories/CategoryCreatePage");
  require("./stories/categories/CategoryUpdatePage");
  require("./stories/categories/CategoryListPage");

  // Collections
  require("./stories/collections/CollectionCreatePage");
  require("./stories/collections/CollectionDetailsPage");
  require("./stories/collections/CollectionListPage");

  // Configuration
  require("./stories/configuration/ConfigurationPage");

  // Customers
  // require("./stories/customers/CustomerDetailsPage");
  require("./stories/customers/CustomerListPage");

  // Homepage
  require("./stories/home/HomePage");

  // Staff
  require("./stories/staff/StaffListPage");
  require("./stories/staff/StaffDetailsPage");

  // Pages
  require("./stories/pages/PageContent");
  require("./stories/pages/PageDeleteDialog");
  require("./stories/pages/PageDetailsPage");
  require("./stories/pages/PageListPage");
  require("./stories/pages/PageProperties");

  // Products
  require("./stories/products/ProductCreatePage");
  require("./stories/products/ProductImagePage");
  require("./stories/products/ProductListCard");
  require("./stories/products/ProductUpdatePage");
  require("./stories/products/ProductVariantCreatePage");
  require("./stories/products/ProductVariantPage");

  // Orders
  require("./stories/orders/OrderAddressEditDialog");
  require("./stories/orders/OrderCancelDialog");
  require("./stories/orders/OrderCustomer");
  require("./stories/orders/OrderCustomerEditDialog");
  require("./stories/orders/OrderDetailsPage");
  require("./stories/orders/OrderDraftPage");
  require("./stories/orders/OrderFulfillmentCancelDialog");
  require("./stories/orders/OrderFulfillmentDialog");
  require("./stories/orders/OrderFulfillmentTrackingDialog");
  require("./stories/orders/OrderHistory");
  require("./stories/orders/OrderListPage");
  require("./stories/orders/OrderPaymentDialog");
  require("./stories/orders/OrderPaymentReleaseDialog");
  require("./stories/orders/OrderProductAddDialog");
  require("./stories/orders/OrderShippingMethodEditDialog");

  // Vouchers
  require("./stories/vouchers/VoucherDetailsPage");
  require("./stories/vouchers/VoucherListPage");

  // Product types
  require("./stories/productTypes/ProductTypeAttributeEditDialog");
  require("./stories/productTypes/ProductTypeCreatePage");
  require("./stories/productTypes/ProductTypeDetailsPage");
  require("./stories/productTypes/ProductTypeListPage");

  // Site settings
  require("./stories/siteSettings/SiteSettingsKeyDialog");
  require("./stories/siteSettings/SiteSettingsPage");
}

configure(loadStories, module);
