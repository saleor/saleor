/* tslint:disable */
// This file was automatically generated and should not be edited.

import { OrderEventsEmails, OrderEvents, FulfillmentStatus, PaymentChargeStatusEnum, OrderStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderRelease
// ====================================================

export interface OrderRelease_orderRelease_order_billingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderRelease_orderRelease_order_billingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderRelease_orderRelease_order_billingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderRelease_orderRelease_order_events_user {
  __typename: "User";
  email: string;
}

export interface OrderRelease_orderRelease_order_events {
  __typename: "OrderEvent";
  id: string;
  amount: number | null;
  date: any | null;
  email: string | null;
  emailType: OrderEventsEmails | null;
  message: string | null;
  quantity: number | null;
  type: OrderEvents | null;
  user: OrderRelease_orderRelease_order_events_user | null;
}

export interface OrderRelease_orderRelease_order_fulfillments_lines_edges_node_orderLine_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderRelease_orderRelease_order_fulfillments_lines_edges_node_orderLine_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderRelease_orderRelease_order_fulfillments_lines_edges_node_orderLine_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderRelease_orderRelease_order_fulfillments_lines_edges_node_orderLine_unitPrice_gross;
  net: OrderRelease_orderRelease_order_fulfillments_lines_edges_node_orderLine_unitPrice_net;
}

export interface OrderRelease_orderRelease_order_fulfillments_lines_edges_node_orderLine {
  __typename: "OrderLine";
  id: string;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderRelease_orderRelease_order_fulfillments_lines_edges_node_orderLine_unitPrice | null;
  thumbnailUrl: string | null;
}

export interface OrderRelease_orderRelease_order_fulfillments_lines_edges_node {
  __typename: "FulfillmentLine";
  id: string;
  quantity: number;
  orderLine: OrderRelease_orderRelease_order_fulfillments_lines_edges_node_orderLine | null;
}

export interface OrderRelease_orderRelease_order_fulfillments_lines_edges {
  __typename: "FulfillmentLineCountableEdge";
  node: OrderRelease_orderRelease_order_fulfillments_lines_edges_node;
}

export interface OrderRelease_orderRelease_order_fulfillments_lines {
  __typename: "FulfillmentLineCountableConnection";
  edges: OrderRelease_orderRelease_order_fulfillments_lines_edges[];
}

export interface OrderRelease_orderRelease_order_fulfillments {
  __typename: "Fulfillment";
  id: string;
  lines: OrderRelease_orderRelease_order_fulfillments_lines | null;
  fulfillmentOrder: number;
  status: FulfillmentStatus;
  trackingNumber: string;
}

export interface OrderRelease_orderRelease_order_lines_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderRelease_orderRelease_order_lines_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderRelease_orderRelease_order_lines_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderRelease_orderRelease_order_lines_unitPrice_gross;
  net: OrderRelease_orderRelease_order_lines_unitPrice_net;
}

export interface OrderRelease_orderRelease_order_lines {
  __typename: "OrderLine";
  id: string;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderRelease_orderRelease_order_lines_unitPrice | null;
  thumbnailUrl: string | null;
}

export interface OrderRelease_orderRelease_order_shippingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderRelease_orderRelease_order_shippingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderRelease_orderRelease_order_shippingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderRelease_orderRelease_order_shippingMethod {
  __typename: "ShippingMethod";
  id: string;
}

export interface OrderRelease_orderRelease_order_shippingPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderRelease_orderRelease_order_shippingPrice {
  __typename: "TaxedMoney";
  gross: OrderRelease_orderRelease_order_shippingPrice_gross;
}

export interface OrderRelease_orderRelease_order_subtotal_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderRelease_orderRelease_order_subtotal {
  __typename: "TaxedMoney";
  gross: OrderRelease_orderRelease_order_subtotal_gross;
}

export interface OrderRelease_orderRelease_order_total_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderRelease_orderRelease_order_total_tax {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderRelease_orderRelease_order_total {
  __typename: "TaxedMoney";
  gross: OrderRelease_orderRelease_order_total_gross;
  tax: OrderRelease_orderRelease_order_total_tax;
}

export interface OrderRelease_orderRelease_order_totalAuthorized {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderRelease_orderRelease_order_totalCaptured {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderRelease_orderRelease_order_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderRelease_orderRelease_order_availableShippingMethods_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderRelease_orderRelease_order_availableShippingMethods {
  __typename: "ShippingMethod";
  id: string;
  name: string;
  price: OrderRelease_orderRelease_order_availableShippingMethods_price | null;
}

export interface OrderRelease_orderRelease_order {
  __typename: "Order";
  id: string;
  billingAddress: OrderRelease_orderRelease_order_billingAddress | null;
  created: any;
  events: (OrderRelease_orderRelease_order_events | null)[] | null;
  fulfillments: (OrderRelease_orderRelease_order_fulfillments | null)[];
  lines: (OrderRelease_orderRelease_order_lines | null)[];
  number: string | null;
  paymentStatus: PaymentChargeStatusEnum | null;
  shippingAddress: OrderRelease_orderRelease_order_shippingAddress | null;
  shippingMethod: OrderRelease_orderRelease_order_shippingMethod | null;
  shippingMethodName: string | null;
  shippingPrice: OrderRelease_orderRelease_order_shippingPrice | null;
  status: OrderStatus;
  subtotal: OrderRelease_orderRelease_order_subtotal | null;
  total: OrderRelease_orderRelease_order_total | null;
  totalAuthorized: OrderRelease_orderRelease_order_totalAuthorized | null;
  totalCaptured: OrderRelease_orderRelease_order_totalCaptured | null;
  user: OrderRelease_orderRelease_order_user | null;
  userEmail: string | null;
  availableShippingMethods: (OrderRelease_orderRelease_order_availableShippingMethods | null)[] | null;
}

export interface OrderRelease_orderRelease {
  __typename: "OrderRelease";
  order: OrderRelease_orderRelease_order | null;
}

export interface OrderRelease {
  orderRelease: OrderRelease_orderRelease | null;
}

export interface OrderReleaseVariables {
  id: string;
}
