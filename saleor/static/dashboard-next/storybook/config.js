/* eslint-disable */
import { configure } from "@storybook/react";

function loadStories() {
  // Components
  require("./stories/components/DateFormatter");
  require("./stories/components/EditableTableCell");
  require("./stories/components/ErrorMessageCard");
  require("./stories/components/Money");
  require("./stories/components/MultiSelectField");
  require("./stories/components/PageHeader");
  require("./stories/components/PhoneField");
  require("./stories/components/PriceField");
  require("./stories/components/SingleAutocompleteSelectField");
  require("./stories/components/SingleSelectField");
  require("./stories/components/Skeleton");
  require("./stories/components/StatusLabel");
  require("./stories/components/TablePagination");
  require("./stories/components/Timeline");

  // Categories
  require("./stories/categories/CategoryBaseForm");
  require("./stories/categories/CategoryProducts");
  require("./stories/categories/CategorySubcategories");
  require("./stories/categories/ProductFilters");
  require("./stories/categories/RootCategoryList");

  // Pages
  require("./stories/pages/PageBaseForm");
  require("./stories/pages/PageDeleteDialog");
  require("./stories/pages/PageFilters");
  require("./stories/pages/PageList");

  // Products
  require("./stories/products/ProductAttributesForm");
  require("./stories/products/ProductAvailabilityForm");
  require("./stories/products/ProductCategoryAndCollectionsForm");
  require("./stories/products/ProductCollections");
  require("./stories/products/ProductDescription");
  require("./stories/products/ProductDetailsForm");
  require("./stories/products/ProductDetailsPage");
  require("./stories/products/ProductImagePage");
  require("./stories/products/ProductImages");
  require("./stories/products/ProductListCard");
  require("./stories/products/ProductPriceAndAvailability");
  require("./stories/products/ProductUpdatePage");
  require("./stories/products/ProductVariantAttributes");
  require("./stories/products/ProductVariantDeleteDialog");
  require("./stories/products/ProductVariantImageSelectDialog");
  require("./stories/products/ProductVariantImages");
  require("./stories/products/ProductVariantNavigation");
  require("./stories/products/ProductVariantPage");
  require("./stories/products/ProductVariantPrice");
  require("./stories/products/ProductVariantProduct");
  require("./stories/products/ProductVariantStock");
  require("./stories/products/ProductVariants");

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
  require("./stories/orders/OrderList");
  require("./stories/orders/OrderListPage");
  require("./stories/orders/OrderPaymentDialog");
  require("./stories/orders/OrderPaymentReleaseDialog");
  require("./stories/orders/OrderProductAddDialog");
  require("./stories/orders/OrderShippingMethodEditDialog");
  require("./stories/orders/OrderSummary");
}

configure(loadStories, module);
