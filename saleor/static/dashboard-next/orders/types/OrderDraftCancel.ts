/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { OrderEventsEmailsEnum, OrderEventsEnum, FulfillmentStatus, PaymentChargeStatusEnum, OrderStatus, OrderAction } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderDraftCancel
// ====================================================

export interface OrderDraftCancel_draftOrderDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderDraftCancel_draftOrderDelete_order_billingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_billingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderDraftCancel_draftOrderDelete_order_billingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_events_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_events {
  __typename: "OrderEvent";
  id: string;
  amount: number | null;
  date: any | null;
  email: string | null;
  emailType: OrderEventsEmailsEnum | null;
  message: string | null;
  quantity: number | null;
  type: OrderEventsEnum | null;
  user: OrderDraftCancel_draftOrderDelete_order_events_user | null;
}

export interface OrderDraftCancel_draftOrderDelete_order_fulfillments_lines_orderLine_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_fulfillments_lines_orderLine_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_fulfillments_lines_orderLine_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderDraftCancel_draftOrderDelete_order_fulfillments_lines_orderLine_unitPrice_gross;
  net: OrderDraftCancel_draftOrderDelete_order_fulfillments_lines_orderLine_unitPrice_net;
}

export interface OrderDraftCancel_draftOrderDelete_order_fulfillments_lines_orderLine_thumbnail {
  __typename: "Image";
  url: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_fulfillments_lines_orderLine {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderDraftCancel_draftOrderDelete_order_fulfillments_lines_orderLine_unitPrice | null;
  thumbnail: OrderDraftCancel_draftOrderDelete_order_fulfillments_lines_orderLine_thumbnail | null;
}

export interface OrderDraftCancel_draftOrderDelete_order_fulfillments_lines {
  __typename: "FulfillmentLine";
  id: string;
  quantity: number;
  orderLine: OrderDraftCancel_draftOrderDelete_order_fulfillments_lines_orderLine | null;
}

export interface OrderDraftCancel_draftOrderDelete_order_fulfillments {
  __typename: "Fulfillment";
  id: string;
  lines: (OrderDraftCancel_draftOrderDelete_order_fulfillments_lines | null)[] | null;
  fulfillmentOrder: number;
  status: FulfillmentStatus;
  trackingNumber: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_lines_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_lines_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_lines_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderDraftCancel_draftOrderDelete_order_lines_unitPrice_gross;
  net: OrderDraftCancel_draftOrderDelete_order_lines_unitPrice_net;
}

export interface OrderDraftCancel_draftOrderDelete_order_lines_thumbnail {
  __typename: "Image";
  url: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_lines {
  __typename: "OrderLine";
  id: string;
  isShippingRequired: boolean;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderDraftCancel_draftOrderDelete_order_lines_unitPrice | null;
  thumbnail: OrderDraftCancel_draftOrderDelete_order_lines_thumbnail | null;
}

export interface OrderDraftCancel_draftOrderDelete_order_shippingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_shippingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderDraftCancel_draftOrderDelete_order_shippingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_shippingMethod {
  __typename: "ShippingMethod";
  id: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_shippingPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_shippingPrice {
  __typename: "TaxedMoney";
  gross: OrderDraftCancel_draftOrderDelete_order_shippingPrice_gross;
}

export interface OrderDraftCancel_draftOrderDelete_order_subtotal_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_subtotal {
  __typename: "TaxedMoney";
  gross: OrderDraftCancel_draftOrderDelete_order_subtotal_gross;
}

export interface OrderDraftCancel_draftOrderDelete_order_total_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_total_tax {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_total {
  __typename: "TaxedMoney";
  gross: OrderDraftCancel_draftOrderDelete_order_total_gross;
  tax: OrderDraftCancel_draftOrderDelete_order_total_tax;
}

export interface OrderDraftCancel_draftOrderDelete_order_totalAuthorized {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_totalCaptured {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_availableShippingMethods_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftCancel_draftOrderDelete_order_availableShippingMethods {
  __typename: "ShippingMethod";
  id: string;
  name: string;
  price: OrderDraftCancel_draftOrderDelete_order_availableShippingMethods_price | null;
}

export interface OrderDraftCancel_draftOrderDelete_order {
  __typename: "Order";
  id: string;
  billingAddress: OrderDraftCancel_draftOrderDelete_order_billingAddress | null;
  canFinalize: boolean;
  created: any;
  customerNote: string;
  events: (OrderDraftCancel_draftOrderDelete_order_events | null)[] | null;
  fulfillments: (OrderDraftCancel_draftOrderDelete_order_fulfillments | null)[];
  lines: (OrderDraftCancel_draftOrderDelete_order_lines | null)[];
  number: string | null;
  paymentStatus: PaymentChargeStatusEnum | null;
  shippingAddress: OrderDraftCancel_draftOrderDelete_order_shippingAddress | null;
  shippingMethod: OrderDraftCancel_draftOrderDelete_order_shippingMethod | null;
  shippingMethodName: string | null;
  shippingPrice: OrderDraftCancel_draftOrderDelete_order_shippingPrice | null;
  status: OrderStatus;
  subtotal: OrderDraftCancel_draftOrderDelete_order_subtotal | null;
  total: OrderDraftCancel_draftOrderDelete_order_total | null;
  actions: (OrderAction | null)[];
  totalAuthorized: OrderDraftCancel_draftOrderDelete_order_totalAuthorized | null;
  totalCaptured: OrderDraftCancel_draftOrderDelete_order_totalCaptured | null;
  user: OrderDraftCancel_draftOrderDelete_order_user | null;
  userEmail: string | null;
  availableShippingMethods: (OrderDraftCancel_draftOrderDelete_order_availableShippingMethods | null)[] | null;
}

export interface OrderDraftCancel_draftOrderDelete {
  __typename: "DraftOrderDelete";
  errors: OrderDraftCancel_draftOrderDelete_errors[] | null;
  order: OrderDraftCancel_draftOrderDelete_order | null;
}

export interface OrderDraftCancel {
  draftOrderDelete: OrderDraftCancel_draftOrderDelete | null;
}

export interface OrderDraftCancelVariables {
  id: string;
}
