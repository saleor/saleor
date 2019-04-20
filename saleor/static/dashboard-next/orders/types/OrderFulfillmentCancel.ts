/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { FulfillmentCancelInput, OrderEventsEmails, OrderEvents, FulfillmentStatus, PaymentChargeStatusEnum, OrderStatus, OrderAction } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderFulfillmentCancel
// ====================================================

export interface OrderFulfillmentCancel_orderFulfillmentCancel_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_billingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_billingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderFulfillmentCancel_orderFulfillmentCancel_order_billingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_events_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_events {
  __typename: "OrderEvent";
  id: string;
  amount: number | null;
  date: any | null;
  email: string | null;
  emailType: OrderEventsEmails | null;
  message: string | null;
  quantity: number | null;
  type: OrderEvents | null;
  user: OrderFulfillmentCancel_orderFulfillmentCancel_order_events_user | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice_gross;
  net: OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice_net;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine_unitPrice | null;
  thumbnailUrl: string | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines {
  __typename: "FulfillmentLine";
  id: string;
  quantity: number;
  orderLine: OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines_orderLine | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments {
  __typename: "Fulfillment";
  id: string;
  lines: (OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments_lines | null)[] | null;
  fulfillmentOrder: number;
  status: FulfillmentStatus;
  trackingNumber: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice_gross;
  net: OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice_net;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_lines {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderFulfillmentCancel_orderFulfillmentCancel_order_lines_unitPrice | null;
  thumbnailUrl: string | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingMethod {
  __typename: "ShippingMethod";
  id: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingPrice {
  __typename: "TaxedMoney";
  gross: OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingPrice_gross;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_subtotal_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_subtotal {
  __typename: "TaxedMoney";
  gross: OrderFulfillmentCancel_orderFulfillmentCancel_order_subtotal_gross;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_total_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_total_tax {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_total {
  __typename: "TaxedMoney";
  gross: OrderFulfillmentCancel_orderFulfillmentCancel_order_total_gross;
  tax: OrderFulfillmentCancel_orderFulfillmentCancel_order_total_tax;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_totalAuthorized {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_totalCaptured {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_availableShippingMethods_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order_availableShippingMethods {
  __typename: "ShippingMethod";
  id: string;
  name: string;
  price: OrderFulfillmentCancel_orderFulfillmentCancel_order_availableShippingMethods_price | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel_order {
  __typename: "Order";
  id: string;
  billingAddress: OrderFulfillmentCancel_orderFulfillmentCancel_order_billingAddress | null;
  canFinalize: boolean;
  created: any;
  customerNote: string;
  events: (OrderFulfillmentCancel_orderFulfillmentCancel_order_events | null)[] | null;
  fulfillments: (OrderFulfillmentCancel_orderFulfillmentCancel_order_fulfillments | null)[];
  lines: (OrderFulfillmentCancel_orderFulfillmentCancel_order_lines | null)[];
  number: string | null;
  paymentStatus: PaymentChargeStatusEnum | null;
  shippingAddress: OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingAddress | null;
  shippingMethod: OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingMethod | null;
  shippingMethodName: string | null;
  shippingPrice: OrderFulfillmentCancel_orderFulfillmentCancel_order_shippingPrice | null;
  status: OrderStatus;
  subtotal: OrderFulfillmentCancel_orderFulfillmentCancel_order_subtotal | null;
  total: OrderFulfillmentCancel_orderFulfillmentCancel_order_total | null;
  actions: (OrderAction | null)[];
  totalAuthorized: OrderFulfillmentCancel_orderFulfillmentCancel_order_totalAuthorized | null;
  totalCaptured: OrderFulfillmentCancel_orderFulfillmentCancel_order_totalCaptured | null;
  user: OrderFulfillmentCancel_orderFulfillmentCancel_order_user | null;
  userEmail: string | null;
  availableShippingMethods: (OrderFulfillmentCancel_orderFulfillmentCancel_order_availableShippingMethods | null)[] | null;
}

export interface OrderFulfillmentCancel_orderFulfillmentCancel {
  __typename: "FulfillmentCancel";
  errors: OrderFulfillmentCancel_orderFulfillmentCancel_errors[] | null;
  order: OrderFulfillmentCancel_orderFulfillmentCancel_order | null;
}

export interface OrderFulfillmentCancel {
  orderFulfillmentCancel: OrderFulfillmentCancel_orderFulfillmentCancel | null;
}

export interface OrderFulfillmentCancelVariables {
  id: string;
  input: FulfillmentCancelInput;
}
