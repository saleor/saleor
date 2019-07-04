/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { FulfillmentCreateInput, OrderEventsEmailsEnum, OrderEventsEnum, FulfillmentStatus, PaymentChargeStatusEnum, OrderStatus, OrderAction } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderCreateFulfillment
// ====================================================

export interface OrderCreateFulfillment_orderFulfillmentCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_billingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_billingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderCreateFulfillment_orderFulfillmentCreate_order_billingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_events_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_events {
  __typename: "OrderEvent";
  id: string;
  amount: number | null;
  date: any | null;
  email: string | null;
  emailType: OrderEventsEmailsEnum | null;
  message: string | null;
  quantity: number | null;
  type: OrderEventsEnum | null;
  user: OrderCreateFulfillment_orderFulfillmentCreate_order_events_user | null;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines_orderLine_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines_orderLine_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines_orderLine_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines_orderLine_unitPrice_gross;
  net: OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines_orderLine_unitPrice_net;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines_orderLine_thumbnail {
  __typename: "Image";
  url: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines_orderLine {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines_orderLine_unitPrice | null;
  thumbnail: OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines_orderLine_thumbnail | null;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines {
  __typename: "FulfillmentLine";
  id: string;
  quantity: number;
  orderLine: OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines_orderLine | null;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments {
  __typename: "Fulfillment";
  id: string;
  lines: (OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments_lines | null)[] | null;
  fulfillmentOrder: number;
  status: FulfillmentStatus;
  trackingNumber: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_lines_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_lines_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_lines_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderCreateFulfillment_orderFulfillmentCreate_order_lines_unitPrice_gross;
  net: OrderCreateFulfillment_orderFulfillmentCreate_order_lines_unitPrice_net;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_lines_thumbnail {
  __typename: "Image";
  url: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_lines {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderCreateFulfillment_orderFulfillmentCreate_order_lines_unitPrice | null;
  thumbnail: OrderCreateFulfillment_orderFulfillmentCreate_order_lines_thumbnail | null;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_shippingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_shippingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderCreateFulfillment_orderFulfillmentCreate_order_shippingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_shippingMethod {
  __typename: "ShippingMethod";
  id: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_shippingPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_shippingPrice {
  __typename: "TaxedMoney";
  gross: OrderCreateFulfillment_orderFulfillmentCreate_order_shippingPrice_gross;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_subtotal_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_subtotal {
  __typename: "TaxedMoney";
  gross: OrderCreateFulfillment_orderFulfillmentCreate_order_subtotal_gross;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_total_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_total_tax {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_total {
  __typename: "TaxedMoney";
  gross: OrderCreateFulfillment_orderFulfillmentCreate_order_total_gross;
  tax: OrderCreateFulfillment_orderFulfillmentCreate_order_total_tax;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_totalAuthorized {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_totalCaptured {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_availableShippingMethods_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order_availableShippingMethods {
  __typename: "ShippingMethod";
  id: string;
  name: string;
  price: OrderCreateFulfillment_orderFulfillmentCreate_order_availableShippingMethods_price | null;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate_order {
  __typename: "Order";
  id: string;
  billingAddress: OrderCreateFulfillment_orderFulfillmentCreate_order_billingAddress | null;
  canFinalize: boolean;
  created: any;
  customerNote: string;
  events: (OrderCreateFulfillment_orderFulfillmentCreate_order_events | null)[] | null;
  fulfillments: (OrderCreateFulfillment_orderFulfillmentCreate_order_fulfillments | null)[];
  lines: (OrderCreateFulfillment_orderFulfillmentCreate_order_lines | null)[];
  number: string | null;
  paymentStatus: PaymentChargeStatusEnum | null;
  shippingAddress: OrderCreateFulfillment_orderFulfillmentCreate_order_shippingAddress | null;
  shippingMethod: OrderCreateFulfillment_orderFulfillmentCreate_order_shippingMethod | null;
  shippingMethodName: string | null;
  shippingPrice: OrderCreateFulfillment_orderFulfillmentCreate_order_shippingPrice | null;
  status: OrderStatus;
  subtotal: OrderCreateFulfillment_orderFulfillmentCreate_order_subtotal | null;
  total: OrderCreateFulfillment_orderFulfillmentCreate_order_total | null;
  actions: (OrderAction | null)[];
  totalAuthorized: OrderCreateFulfillment_orderFulfillmentCreate_order_totalAuthorized | null;
  totalCaptured: OrderCreateFulfillment_orderFulfillmentCreate_order_totalCaptured | null;
  user: OrderCreateFulfillment_orderFulfillmentCreate_order_user | null;
  userEmail: string | null;
  availableShippingMethods: (OrderCreateFulfillment_orderFulfillmentCreate_order_availableShippingMethods | null)[] | null;
}

export interface OrderCreateFulfillment_orderFulfillmentCreate {
  __typename: "FulfillmentCreate";
  errors: OrderCreateFulfillment_orderFulfillmentCreate_errors[] | null;
  order: OrderCreateFulfillment_orderFulfillmentCreate_order | null;
}

export interface OrderCreateFulfillment {
  orderFulfillmentCreate: OrderCreateFulfillment_orderFulfillmentCreate | null;
}

export interface OrderCreateFulfillmentVariables {
  order: string;
  input: FulfillmentCreateInput;
}
