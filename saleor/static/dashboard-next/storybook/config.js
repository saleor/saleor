/* eslint-disable */
import { configure } from "@storybook/react";

function loadStories() {
  // Components
  require("./stories/components/ActionDialog");
  require("./stories/components/AddressEdit");
  require("./stories/components/AddressFormatter");
  require("./stories/components/DateFormatter");
  require("./stories/components/EditableTableCell");
  require("./stories/components/ErrorMessageCard");
  require("./stories/components/Money");
  require("./stories/components/MultiAutocompleteSelectField");
  require("./stories/components/MultiSelectField");
  require("./stories/components/PageHeader");
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

  // Attributes
  require("./stories/attributes/AttributeDetailsPage");
  require("./stories/attributes/AttributeListPage");

  // Categories
  require("./stories/categories/CategoryDeleteDialog");
  require("./stories/categories/CategoryDetailsPage");
  require("./stories/categories/CategoryEditPage");
  require("./stories/categories/CategoryProducts");

  // Collections
  require("./stories/collections/CollectionDetailsPage");
  require("./stories/collections/CollectionListPage");

  // Customers
  require("./stories/customers/CustomerDetailsPage");
  require("./stories/customers/CustomerEditPage");
  require("./stories/customers/CustomerListPage");

  // Pages
  require("./stories/pages/PageContent");
  require("./stories/pages/PageDeleteDialog");
  require("./stories/pages/PageDetailsPage");
  require("./stories/pages/PageListPage");
  require("./stories/pages/PageProperties");

  // Products
  require("./stories/products/ProductImagePage");
  require("./stories/products/ProductListCard");
  require("./stories/products/ProductUpdatePage");
  require("./stories/products/ProductVariantPage");

  // Orders
  require("./stories/orders/OrderAddressEditDialog");
  require("./stories/orders/OrderCancelDialog");
  require("./stories/orders/OrderCustomer");
  require("./stories/orders/OrderCustomerEditDialog");
  require("./stories/orders/OrderDetailsPage");
  require("./stories/orders/OrderFulfillmentCancelDialog");
  require("./stories/orders/OrderFulfillmentDialog");
  require("./stories/orders/OrderFulfillmentTrackingDialog");
  require("./stories/orders/OrderHistory");
  require("./stories/orders/OrderListPage");
  require("./stories/orders/OrderPaymentDialog");
  require("./stories/orders/OrderPaymentReleaseDialog");
  require("./stories/orders/OrderProductAddDialog");
  require("./stories/orders/OrderShippingMethodEditDialog");
  require("./stories/orders/OrderSummary");

  // Vouchers
  require("./stories/vouchers/VoucherDetailsPage");
  require("./stories/vouchers/VoucherListPage");

  // Product types
  require("./stories/productTypes/ProductTypeListPage");
  require("./stories/productTypes/ProductTypeDetailsPage");
}

configure(loadStories, module);
