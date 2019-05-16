/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { OrderLineCreateInput, OrderEventsEmailsEnum, OrderEventsEnum, FulfillmentStatus, PaymentChargeStatusEnum, OrderStatus, OrderAction } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderLinesAdd
// ====================================================

export interface OrderLinesAdd_draftOrderLinesCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_billingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_billingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderLinesAdd_draftOrderLinesCreate_order_billingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_events_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_events {
  __typename: "OrderEvent";
  id: string;
  amount: number | null;
  date: any | null;
  email: string | null;
  emailType: OrderEventsEmailsEnum | null;
  message: string | null;
  quantity: number | null;
  type: OrderEventsEnum | null;
  user: OrderLinesAdd_draftOrderLinesCreate_order_events_user | null;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines_orderLine_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines_orderLine_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines_orderLine_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines_orderLine_unitPrice_gross;
  net: OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines_orderLine_unitPrice_net;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines_orderLine_thumbnail {
  __typename: "Image";
  url: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines_orderLine {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines_orderLine_unitPrice | null;
  thumbnail: OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines_orderLine_thumbnail | null;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines {
  __typename: "FulfillmentLine";
  id: string;
  quantity: number;
  orderLine: OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines_orderLine | null;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_fulfillments {
  __typename: "Fulfillment";
  id: string;
  lines: (OrderLinesAdd_draftOrderLinesCreate_order_fulfillments_lines | null)[] | null;
  fulfillmentOrder: number;
  status: FulfillmentStatus;
  trackingNumber: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_lines_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_lines_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_lines_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderLinesAdd_draftOrderLinesCreate_order_lines_unitPrice_gross;
  net: OrderLinesAdd_draftOrderLinesCreate_order_lines_unitPrice_net;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_lines_thumbnail {
  __typename: "Image";
  url: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_lines {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderLinesAdd_draftOrderLinesCreate_order_lines_unitPrice | null;
  thumbnail: OrderLinesAdd_draftOrderLinesCreate_order_lines_thumbnail | null;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_shippingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_shippingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderLinesAdd_draftOrderLinesCreate_order_shippingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_shippingMethod {
  __typename: "ShippingMethod";
  id: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_shippingPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_shippingPrice {
  __typename: "TaxedMoney";
  gross: OrderLinesAdd_draftOrderLinesCreate_order_shippingPrice_gross;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_subtotal_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_subtotal {
  __typename: "TaxedMoney";
  gross: OrderLinesAdd_draftOrderLinesCreate_order_subtotal_gross;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_total_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_total_tax {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_total {
  __typename: "TaxedMoney";
  gross: OrderLinesAdd_draftOrderLinesCreate_order_total_gross;
  tax: OrderLinesAdd_draftOrderLinesCreate_order_total_tax;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_totalAuthorized {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_totalCaptured {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_availableShippingMethods_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order_availableShippingMethods {
  __typename: "ShippingMethod";
  id: string;
  name: string;
  price: OrderLinesAdd_draftOrderLinesCreate_order_availableShippingMethods_price | null;
}

export interface OrderLinesAdd_draftOrderLinesCreate_order {
  __typename: "Order";
  id: string;
  billingAddress: OrderLinesAdd_draftOrderLinesCreate_order_billingAddress | null;
  canFinalize: boolean;
  created: any;
  customerNote: string;
  events: (OrderLinesAdd_draftOrderLinesCreate_order_events | null)[] | null;
  fulfillments: (OrderLinesAdd_draftOrderLinesCreate_order_fulfillments | null)[];
  lines: (OrderLinesAdd_draftOrderLinesCreate_order_lines | null)[];
  number: string | null;
  paymentStatus: PaymentChargeStatusEnum | null;
  shippingAddress: OrderLinesAdd_draftOrderLinesCreate_order_shippingAddress | null;
  shippingMethod: OrderLinesAdd_draftOrderLinesCreate_order_shippingMethod | null;
  shippingMethodName: string | null;
  shippingPrice: OrderLinesAdd_draftOrderLinesCreate_order_shippingPrice | null;
  status: OrderStatus;
  subtotal: OrderLinesAdd_draftOrderLinesCreate_order_subtotal | null;
  total: OrderLinesAdd_draftOrderLinesCreate_order_total | null;
  actions: (OrderAction | null)[];
  totalAuthorized: OrderLinesAdd_draftOrderLinesCreate_order_totalAuthorized | null;
  totalCaptured: OrderLinesAdd_draftOrderLinesCreate_order_totalCaptured | null;
  user: OrderLinesAdd_draftOrderLinesCreate_order_user | null;
  userEmail: string | null;
  availableShippingMethods: (OrderLinesAdd_draftOrderLinesCreate_order_availableShippingMethods | null)[] | null;
}

export interface OrderLinesAdd_draftOrderLinesCreate {
  __typename: "DraftOrderLinesCreate";
  errors: OrderLinesAdd_draftOrderLinesCreate_errors[] | null;
  order: OrderLinesAdd_draftOrderLinesCreate_order | null;
}

export interface OrderLinesAdd {
  draftOrderLinesCreate: OrderLinesAdd_draftOrderLinesCreate | null;
}

export interface OrderLinesAddVariables {
  id: string;
  input: (OrderLineCreateInput | null)[];
}
