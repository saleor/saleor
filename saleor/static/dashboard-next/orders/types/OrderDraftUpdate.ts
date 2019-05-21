/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { DraftOrderInput, OrderEventsEmailsEnum, OrderEventsEnum, FulfillmentStatus, PaymentChargeStatusEnum, OrderStatus, OrderAction } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderDraftUpdate
// ====================================================

export interface OrderDraftUpdate_draftOrderUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_billingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_billingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderDraftUpdate_draftOrderUpdate_order_billingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_events_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_events {
  __typename: "OrderEvent";
  id: string;
  amount: number | null;
  date: any | null;
  email: string | null;
  emailType: OrderEventsEmailsEnum | null;
  message: string | null;
  quantity: number | null;
  type: OrderEventsEnum | null;
  user: OrderDraftUpdate_draftOrderUpdate_order_events_user | null;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines_orderLine_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines_orderLine_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines_orderLine_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines_orderLine_unitPrice_gross;
  net: OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines_orderLine_unitPrice_net;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines_orderLine_thumbnail {
  __typename: "Image";
  url: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines_orderLine {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines_orderLine_unitPrice | null;
  thumbnail: OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines_orderLine_thumbnail | null;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines {
  __typename: "FulfillmentLine";
  id: string;
  quantity: number;
  orderLine: OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines_orderLine | null;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_fulfillments {
  __typename: "Fulfillment";
  id: string;
  lines: (OrderDraftUpdate_draftOrderUpdate_order_fulfillments_lines | null)[] | null;
  fulfillmentOrder: number;
  status: FulfillmentStatus;
  trackingNumber: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_lines_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_lines_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_lines_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderDraftUpdate_draftOrderUpdate_order_lines_unitPrice_gross;
  net: OrderDraftUpdate_draftOrderUpdate_order_lines_unitPrice_net;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_lines_thumbnail {
  __typename: "Image";
  url: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_lines {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderDraftUpdate_draftOrderUpdate_order_lines_unitPrice | null;
  thumbnail: OrderDraftUpdate_draftOrderUpdate_order_lines_thumbnail | null;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_shippingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_shippingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderDraftUpdate_draftOrderUpdate_order_shippingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_shippingMethod {
  __typename: "ShippingMethod";
  id: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_shippingPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_shippingPrice {
  __typename: "TaxedMoney";
  gross: OrderDraftUpdate_draftOrderUpdate_order_shippingPrice_gross;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_subtotal_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_subtotal {
  __typename: "TaxedMoney";
  gross: OrderDraftUpdate_draftOrderUpdate_order_subtotal_gross;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_total_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_total_tax {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_total {
  __typename: "TaxedMoney";
  gross: OrderDraftUpdate_draftOrderUpdate_order_total_gross;
  tax: OrderDraftUpdate_draftOrderUpdate_order_total_tax;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_totalAuthorized {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_totalCaptured {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_availableShippingMethods_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftUpdate_draftOrderUpdate_order_availableShippingMethods {
  __typename: "ShippingMethod";
  id: string;
  name: string;
  price: OrderDraftUpdate_draftOrderUpdate_order_availableShippingMethods_price | null;
}

export interface OrderDraftUpdate_draftOrderUpdate_order {
  __typename: "Order";
  id: string;
  billingAddress: OrderDraftUpdate_draftOrderUpdate_order_billingAddress | null;
  canFinalize: boolean;
  created: any;
  customerNote: string;
  events: (OrderDraftUpdate_draftOrderUpdate_order_events | null)[] | null;
  fulfillments: (OrderDraftUpdate_draftOrderUpdate_order_fulfillments | null)[];
  lines: (OrderDraftUpdate_draftOrderUpdate_order_lines | null)[];
  number: string | null;
  paymentStatus: PaymentChargeStatusEnum | null;
  shippingAddress: OrderDraftUpdate_draftOrderUpdate_order_shippingAddress | null;
  shippingMethod: OrderDraftUpdate_draftOrderUpdate_order_shippingMethod | null;
  shippingMethodName: string | null;
  shippingPrice: OrderDraftUpdate_draftOrderUpdate_order_shippingPrice | null;
  status: OrderStatus;
  subtotal: OrderDraftUpdate_draftOrderUpdate_order_subtotal | null;
  total: OrderDraftUpdate_draftOrderUpdate_order_total | null;
  actions: (OrderAction | null)[];
  totalAuthorized: OrderDraftUpdate_draftOrderUpdate_order_totalAuthorized | null;
  totalCaptured: OrderDraftUpdate_draftOrderUpdate_order_totalCaptured | null;
  user: OrderDraftUpdate_draftOrderUpdate_order_user | null;
  userEmail: string | null;
  availableShippingMethods: (OrderDraftUpdate_draftOrderUpdate_order_availableShippingMethods | null)[] | null;
}

export interface OrderDraftUpdate_draftOrderUpdate {
  __typename: "DraftOrderUpdate";
  errors: OrderDraftUpdate_draftOrderUpdate_errors[] | null;
  order: OrderDraftUpdate_draftOrderUpdate_order | null;
}

export interface OrderDraftUpdate {
  draftOrderUpdate: OrderDraftUpdate_draftOrderUpdate | null;
}

export interface OrderDraftUpdateVariables {
  id: string;
  input: DraftOrderInput;
}
