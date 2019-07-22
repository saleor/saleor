/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { OrderEventsEmailsEnum, OrderEventsEnum, FulfillmentStatus, PaymentChargeStatusEnum, OrderStatus, OrderAction, WeightUnitsEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: OrderDetails
// ====================================================

export interface OrderDetails_order_billingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderDetails_order_billingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderDetails_order_billingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderDetails_order_events_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderDetails_order_events {
  __typename: "OrderEvent";
  id: string;
  amount: number | null;
  date: any | null;
  email: string | null;
  emailType: OrderEventsEmailsEnum | null;
  message: string | null;
  quantity: number | null;
  type: OrderEventsEnum | null;
  user: OrderDetails_order_events_user | null;
}

export interface OrderDetails_order_fulfillments_lines_orderLine_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDetails_order_fulfillments_lines_orderLine_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDetails_order_fulfillments_lines_orderLine_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderDetails_order_fulfillments_lines_orderLine_unitPrice_gross;
  net: OrderDetails_order_fulfillments_lines_orderLine_unitPrice_net;
}

export interface OrderDetails_order_fulfillments_lines_orderLine_thumbnail {
  __typename: "Image";
  url: string;
}

export interface OrderDetails_order_fulfillments_lines_orderLine {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderDetails_order_fulfillments_lines_orderLine_unitPrice | null;
  thumbnail: OrderDetails_order_fulfillments_lines_orderLine_thumbnail | null;
}

export interface OrderDetails_order_fulfillments_lines {
  __typename: "FulfillmentLine";
  id: string;
  quantity: number;
  orderLine: OrderDetails_order_fulfillments_lines_orderLine | null;
}

export interface OrderDetails_order_fulfillments {
  __typename: "Fulfillment";
  id: string;
  lines: (OrderDetails_order_fulfillments_lines | null)[] | null;
  fulfillmentOrder: number;
  status: FulfillmentStatus;
  trackingNumber: string;
}

export interface OrderDetails_order_lines_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDetails_order_lines_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDetails_order_lines_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderDetails_order_lines_unitPrice_gross;
  net: OrderDetails_order_lines_unitPrice_net;
}

export interface OrderDetails_order_lines_thumbnail {
  __typename: "Image";
  url: string;
}

export interface OrderDetails_order_lines {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderDetails_order_lines_unitPrice | null;
  thumbnail: OrderDetails_order_lines_thumbnail | null;
}

export interface OrderDetails_order_shippingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderDetails_order_shippingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderDetails_order_shippingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderDetails_order_shippingMethod {
  __typename: "ShippingMethod";
  id: string;
}

export interface OrderDetails_order_shippingPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDetails_order_shippingPrice {
  __typename: "TaxedMoney";
  gross: OrderDetails_order_shippingPrice_gross;
}

export interface OrderDetails_order_subtotal_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDetails_order_subtotal {
  __typename: "TaxedMoney";
  gross: OrderDetails_order_subtotal_gross;
}

export interface OrderDetails_order_total_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDetails_order_total_tax {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDetails_order_total {
  __typename: "TaxedMoney";
  gross: OrderDetails_order_total_gross;
  tax: OrderDetails_order_total_tax;
}

export interface OrderDetails_order_totalAuthorized {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDetails_order_totalCaptured {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDetails_order_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderDetails_order_availableShippingMethods_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDetails_order_availableShippingMethods {
  __typename: "ShippingMethod";
  id: string;
  name: string;
  price: OrderDetails_order_availableShippingMethods_price | null;
}

export interface OrderDetails_order {
  __typename: "Order";
  id: string;
  billingAddress: OrderDetails_order_billingAddress | null;
  canFinalize: boolean;
  created: any;
  customerNote: string;
  events: (OrderDetails_order_events | null)[] | null;
  fulfillments: (OrderDetails_order_fulfillments | null)[];
  lines: (OrderDetails_order_lines | null)[];
  number: string | null;
  paymentStatus: PaymentChargeStatusEnum | null;
  shippingAddress: OrderDetails_order_shippingAddress | null;
  shippingMethod: OrderDetails_order_shippingMethod | null;
  shippingMethodName: string | null;
  shippingPrice: OrderDetails_order_shippingPrice | null;
  status: OrderStatus;
  subtotal: OrderDetails_order_subtotal | null;
  total: OrderDetails_order_total | null;
  actions: (OrderAction | null)[];
  totalAuthorized: OrderDetails_order_totalAuthorized | null;
  totalCaptured: OrderDetails_order_totalCaptured | null;
  user: OrderDetails_order_user | null;
  userEmail: string | null;
  availableShippingMethods: (OrderDetails_order_availableShippingMethods | null)[] | null;
}

export interface OrderDetails_shop_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderDetails_shop {
  __typename: "Shop";
  countries: (OrderDetails_shop_countries | null)[];
  defaultWeightUnit: WeightUnitsEnum | null;
}

export interface OrderDetails {
  order: OrderDetails_order | null;
  shop: OrderDetails_shop | null;
}

export interface OrderDetailsVariables {
  id: string;
}
