/* tslint:disable */
// This file was automatically generated and should not be edited.

//==============================================================
// START Enums and Input Objects
//==============================================================

export enum AttributeTypeEnum {
  PRODUCT = "PRODUCT",
  VARIANT = "VARIANT",
}

export enum AuthorizationKeyType {
  FACEBOOK = "FACEBOOK",
  GOOGLE_OAUTH2 = "GOOGLE_OAUTH2",
}

export enum FulfillmentStatus {
  CANCELED = "CANCELED",
  FULFILLED = "FULFILLED",
}

export enum OrderEvents {
  CANCELED = "CANCELED",
  EMAIL_SENT = "EMAIL_SENT",
  FULFILLMENT_CANCELED = "FULFILLMENT_CANCELED",
  FULFILLMENT_FULFILLED_ITEMS = "FULFILLMENT_FULFILLED_ITEMS",
  FULFILLMENT_RESTOCKED_ITEMS = "FULFILLMENT_RESTOCKED_ITEMS",
  NOTE_ADDED = "NOTE_ADDED",
  ORDER_FULLY_PAID = "ORDER_FULLY_PAID",
  ORDER_MARKED_AS_PAID = "ORDER_MARKED_AS_PAID",
  OTHER = "OTHER",
  OVERSOLD_ITEMS = "OVERSOLD_ITEMS",
  PAYMENT_CAPTURED = "PAYMENT_CAPTURED",
  PAYMENT_REFUNDED = "PAYMENT_REFUNDED",
  PAYMENT_RELEASED = "PAYMENT_RELEASED",
  PLACED = "PLACED",
  PLACED_FROM_DRAFT = "PLACED_FROM_DRAFT",
  TRACKING_UPDATED = "TRACKING_UPDATED",
  UPDATED = "UPDATED",
}

export enum OrderEventsEmails {
  FULFILLMENT = "FULFILLMENT",
  ORDER = "ORDER",
  PAYMENT = "PAYMENT",
  SHIPPING = "SHIPPING",
}

export enum OrderStatus {
  CANCELED = "CANCELED",
  DRAFT = "DRAFT",
  FULFILLED = "FULFILLED",
  PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED",
  UNFULFILLED = "UNFULFILLED",
}

export enum PaymentStatusEnum {
  CONFIRMED = "CONFIRMED",
  ERROR = "ERROR",
  INPUT = "INPUT",
  PREAUTH = "PREAUTH",
  REFUNDED = "REFUNDED",
  REJECTED = "REJECTED",
  WAITING = "WAITING",
}

export enum PermissionEnum {
  IMPERSONATE_USERS = "IMPERSONATE_USERS",
  MANAGE_DISCOUNTS = "MANAGE_DISCOUNTS",
  MANAGE_MENUS = "MANAGE_MENUS",
  MANAGE_ORDERS = "MANAGE_ORDERS",
  MANAGE_PAGES = "MANAGE_PAGES",
  MANAGE_PRODUCTS = "MANAGE_PRODUCTS",
  MANAGE_SETTINGS = "MANAGE_SETTINGS",
  MANAGE_SHIPPING = "MANAGE_SHIPPING",
  MANAGE_STAFF = "MANAGE_STAFF",
  MANAGE_USERS = "MANAGE_USERS",
}

export enum TaxRateType {
  ACCOMMODATION = "ACCOMMODATION",
  ADMISSION_TO_CULTURAL_EVENTS = "ADMISSION_TO_CULTURAL_EVENTS",
  ADMISSION_TO_ENTERTAINMENT_EVENTS = "ADMISSION_TO_ENTERTAINMENT_EVENTS",
  ADMISSION_TO_SPORTING_EVENTS = "ADMISSION_TO_SPORTING_EVENTS",
  ADVERTISING = "ADVERTISING",
  AGRICULTURAL_SUPPLIES = "AGRICULTURAL_SUPPLIES",
  BABY_FOODSTUFFS = "BABY_FOODSTUFFS",
  BIKES = "BIKES",
  BOOKS = "BOOKS",
  CHILDRENS_CLOTHING = "CHILDRENS_CLOTHING",
  DOMESTIC_FUEL = "DOMESTIC_FUEL",
  DOMESTIC_SERVICES = "DOMESTIC_SERVICES",
  E_BOOKS = "E_BOOKS",
  FOODSTUFFS = "FOODSTUFFS",
  HOTELS = "HOTELS",
  MEDICAL = "MEDICAL",
  NEWSPAPERS = "NEWSPAPERS",
  PASSENGER_TRANSPORT = "PASSENGER_TRANSPORT",
  PHARMACEUTICALS = "PHARMACEUTICALS",
  PROPERTY_RENOVATIONS = "PROPERTY_RENOVATIONS",
  RESTAURANTS = "RESTAURANTS",
  SOCIAL_HOUSING = "SOCIAL_HOUSING",
  STANDARD = "STANDARD",
  WATER = "WATER",
}

export enum WeightUnitsEnum {
  g = "g",
  kg = "kg",
  lb = "lb",
  oz = "oz",
}

export interface AddressInput {
  firstName?: string | null;
  lastName?: string | null;
  companyName?: string | null;
  streetAddress1?: string | null;
  streetAddress2?: string | null;
  city?: string | null;
  cityArea?: string | null;
  postalCode?: string | null;
  country?: string | null;
  countryArea?: string | null;
  phone?: string | null;
}

export interface AttributeCreateInput {
  name: string;
  values?: (AttributeValueCreateInput | null)[] | null;
}

export interface AttributeUpdateInput {
  name?: string | null;
  removeValues?: (string | null)[] | null;
  addValues?: (AttributeValueCreateInput | null)[] | null;
}

export interface AttributeValueCreateInput {
  name: string;
  value?: string | null;
}

export interface AttributeValueInput {
  slug: string;
  value: string;
}

export interface AuthorizationKeyInput {
  key: string;
  password: string;
}

export interface CategoryInput {
  description?: string | null;
  name?: string | null;
  slug?: string | null;
  seo?: SeoInput | null;
  backgroundImage?: any | null;
}

export interface CollectionCreateInput {
  isPublished?: boolean | null;
  name?: string | null;
  slug?: string | null;
  backgroundImage?: any | null;
  seo?: SeoInput | null;
  products?: (string | null)[] | null;
}

export interface CollectionInput {
  isPublished?: boolean | null;
  name?: string | null;
  slug?: string | null;
  backgroundImage?: any | null;
  seo?: SeoInput | null;
}

export interface DraftOrderInput {
  billingAddress?: AddressInput | null;
  user?: string | null;
  userEmail?: string | null;
  discount?: any | null;
  shippingAddress?: AddressInput | null;
  shippingMethod?: string | null;
  voucher?: string | null;
}

export interface FulfillmentCancelInput {
  restock?: boolean | null;
}

export interface FulfillmentCreateInput {
  trackingNumber?: string | null;
  notifyCustomer?: boolean | null;
  lines: (FulfillmentLineInput | null)[];
}

export interface FulfillmentLineInput {
  orderLineId?: string | null;
  quantity?: number | null;
}

export interface FulfillmentUpdateTrackingInput {
  trackingNumber?: string | null;
  notifyCustomer?: boolean | null;
}

export interface OrderAddNoteInput {
  message?: string | null;
}

export interface OrderLineCreateInput {
  quantity: number;
  variantId: string;
}

export interface OrderLineInput {
  quantity: number;
}

export interface OrderUpdateInput {
  billingAddress?: AddressInput | null;
  userEmail?: string | null;
  shippingAddress?: AddressInput | null;
}

export interface OrderUpdateShippingInput {
  shippingMethod?: string | null;
}

export interface ProductTypeInput {
  name?: string | null;
  hasVariants?: boolean | null;
  productAttributes?: (string | null)[] | null;
  variantAttributes?: (string | null)[] | null;
  isShippingRequired?: boolean | null;
  weight?: any | null;
  taxRate?: TaxRateType | null;
}

export interface SeoInput {
  title?: string | null;
  description?: string | null;
}

export interface ShopSettingsInput {
  headerText?: string | null;
  description?: string | null;
  includeTaxesInPrices?: boolean | null;
  displayGrossPrices?: boolean | null;
  trackInventoryByDefault?: boolean | null;
  defaultWeightUnit?: WeightUnitsEnum | null;
}

export interface SiteDomainInput {
  domain?: string | null;
  name?: string | null;
}

export interface StaffCreateInput {
  email?: string | null;
  note?: string | null;
  isActive?: boolean | null;
  permissions?: (string | null)[] | null;
  sendPasswordEmail?: boolean | null;
}

export interface StaffInput {
  email?: string | null;
  note?: string | null;
  isActive?: boolean | null;
  permissions?: (string | null)[] | null;
}

//==============================================================
// END Enums and Input Objects
//==============================================================
