/* eslint-disable */
configure = require("@storybook/react").configure;

function loadStories() {
  // Components
  require("./stories/components/ActionDialog");
  require("./stories/components/AddressEdit");
  require("./stories/components/AddressFormatter");
  require("./stories/components/CardMenu");
  require("./stories/components/Date");
  require("./stories/components/DateTime");
  require("./stories/components/EditableTableCell");
  require("./stories/components/ErrorMessageCard");
  require("./stories/components/ErrorPage");
  require("./stories/components/ExternalLink");
  require("./stories/components/Money");
  require("./stories/components/MoneyRange");
  require("./stories/components/MultiAutocompleteSelectField");
  require("./stories/components/MultiSelectField");
  require("./stories/components/NotFoundPage");
  require("./stories/components/PageHeader");
  require("./stories/components/Percent");
  require("./stories/components/PhoneField");
  require("./stories/components/PriceField");
  require("./stories/components/RichTextEditor");
  require("./stories/components/SaveButtonBar");
  require("./stories/components/SingleAutocompleteSelectField");
  require("./stories/components/SingleSelectField");
  require("./stories/components/Skeleton");
  require("./stories/components/StatusLabel");
  require("./stories/components/TablePagination");
  require("./stories/components/Timeline");
  require("./stories/components/Weight");
  require("./stories/components/WeightRange");
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
  require("./stories/customers/CustomerAddressDialog");
  require("./stories/customers/CustomerAddressListPage");
  require("./stories/customers/CustomerCreatePage");
  require("./stories/customers/CustomerDetailsPage");
  require("./stories/customers/CustomerListPage");

  // Discounts
  require("./stories/discounts/DiscountCountrySelectDialog");
  require("./stories/discounts/SaleCreatePage");
  require("./stories/discounts/SaleDetailsPage");
  require("./stories/discounts/SaleListPage");
  require("./stories/discounts/VoucherCreatePage");
  require("./stories/discounts/VoucherDetailsPage");
  require("./stories/discounts/VoucherListPage");

  // Homepage
  require("./stories/home/HomePage");

  // Staff
  require("./stories/staff/StaffListPage");
  require("./stories/staff/StaffDetailsPage");

  // Pages
  require("./stories/pages/PageDetailsPage");
  require("./stories/pages/PageListPage");

  // Products
  require("./stories/products/ProductCreatePage");
  require("./stories/products/ProductImagePage");
  require("./stories/products/ProductListCard");
  require("./stories/products/ProductUpdatePage");
  require("./stories/products/ProductVariantCreatePage");
  require("./stories/products/ProductVariantImageSelectDialog");
  require("./stories/products/ProductVariantPage");

  // Orders
  require("./stories/orders/OrderAddressEditDialog");
  require("./stories/orders/OrderBulkCancelDialog");
  require("./stories/orders/OrderCancelDialog");
  require("./stories/orders/OrderCustomer");
  require("./stories/orders/OrderCustomerEditDialog");
  require("./stories/orders/OrderDetailsPage");
  require("./stories/orders/OrderDraftCancelDialog");
  require("./stories/orders/OrderDraftFinalizeDialog");
  require("./stories/orders/OrderDraftListPage");
  require("./stories/orders/OrderDraftPage");
  require("./stories/orders/OrderFulfillmentCancelDialog");
  require("./stories/orders/OrderFulfillmentDialog");
  require("./stories/orders/OrderFulfillmentTrackingDialog");
  require("./stories/orders/OrderHistory");
  require("./stories/orders/OrderListPage");
  require("./stories/orders/OrderMarkAsPaidDialog");
  require("./stories/orders/OrderPaymentDialog");
  require("./stories/orders/OrderPaymentVoidDialog");
  require("./stories/orders/OrderProductAddDialog");
  require("./stories/orders/OrderShippingMethodEditDialog");

  // Product types
  require("./stories/productTypes/ProductTypeAttributeEditDialog");
  require("./stories/productTypes/ProductTypeCreatePage");
  require("./stories/productTypes/ProductTypeDetailsPage");
  require("./stories/productTypes/ProductTypeListPage");

  // Shipping
  require("./stories/shipping/ShippingZoneCountriesAssignDialog");
  require("./stories/shipping/ShippingZoneCreatePage");
  require("./stories/shipping/ShippingZoneDetailsPage");
  require("./stories/shipping/ShippingZoneRateDialog");
  require("./stories/shipping/ShippingZonesListPage");

  // Site settings
  require("./stories/siteSettings/SiteSettingsKeyDialog");
  require("./stories/siteSettings/SiteSettingsPage");

  // Taxes
  require("./stories/taxes/CountryListPage");
  require("./stories/taxes/CountryTaxesPage");

  // Translations
  require("./stories/translations/TranslationsEntitiesListPage");
  require("./stories/translations/TranslationsLanguageListPage");
}

configure(loadStories, module);
