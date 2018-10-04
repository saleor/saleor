/* tslint:disable */
// This file was automatically generated and should not be edited.

import { OrderLineCreateInput, OrderEventsEmails, OrderEvents, FulfillmentStatus, PaymentStatusEnum, OrderStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: OrderLineAdd
// ====================================================

export interface OrderLineAdd_draftOrderLineCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface OrderLineAdd_draftOrderLineCreate_order_billingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_billingAddress {
  __typename: "Address";
  id: string;
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderLineAdd_draftOrderLineCreate_order_billingAddress_country;
  countryArea: string;
  firstName: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_events_user {
  __typename: "User";
  email: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_events {
  __typename: "OrderEvent";
  id: string;
  amount: number | null;
  date: any | null;
  email: string | null;
  emailType: OrderEventsEmails | null;
  message: string | null;
  quantity: number | null;
  type: OrderEvents | null;
  user: OrderLineAdd_draftOrderLineCreate_order_events_user | null;
}

export interface OrderLineAdd_draftOrderLineCreate_order_fulfillments_lines_edges_node_orderLine {
  __typename: "OrderLine";
  id: string;
  productName: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_fulfillments_lines_edges_node {
  __typename: "FulfillmentLine";
  id: string;
  orderLine: OrderLineAdd_draftOrderLineCreate_order_fulfillments_lines_edges_node_orderLine;
  quantity: number;
}

export interface OrderLineAdd_draftOrderLineCreate_order_fulfillments_lines_edges {
  __typename: "FulfillmentLineCountableEdge";
  node: OrderLineAdd_draftOrderLineCreate_order_fulfillments_lines_edges_node;
}

export interface OrderLineAdd_draftOrderLineCreate_order_fulfillments_lines {
  __typename: "FulfillmentLineCountableConnection";
  edges: OrderLineAdd_draftOrderLineCreate_order_fulfillments_lines_edges[];
}

export interface OrderLineAdd_draftOrderLineCreate_order_fulfillments {
  __typename: "Fulfillment";
  id: string;
  lines: OrderLineAdd_draftOrderLineCreate_order_fulfillments_lines | null;
  status: FulfillmentStatus;
  trackingNumber: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_lines_unitPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_lines_unitPrice_net {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_lines_unitPrice {
  __typename: "TaxedMoney";
  gross: OrderLineAdd_draftOrderLineCreate_order_lines_unitPrice_gross;
  net: OrderLineAdd_draftOrderLineCreate_order_lines_unitPrice_net;
}

export interface OrderLineAdd_draftOrderLineCreate_order_lines {
  __typename: "OrderLine";
  id: string;
  productName: string;
  productSku: string;
  quantity: number;
  quantityFulfilled: number;
  unitPrice: OrderLineAdd_draftOrderLineCreate_order_lines_unitPrice | null;
  thumbnailUrl: string | null;
}

export interface OrderLineAdd_draftOrderLineCreate_order_shippingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_shippingAddress {
  __typename: "Address";
  id: string;
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderLineAdd_draftOrderLineCreate_order_shippingAddress_country;
  countryArea: string;
  firstName: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_shippingMethod {
  __typename: "ShippingMethod";
  id: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_shippingPrice_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_shippingPrice {
  __typename: "TaxedMoney";
  gross: OrderLineAdd_draftOrderLineCreate_order_shippingPrice_gross;
}

export interface OrderLineAdd_draftOrderLineCreate_order_subtotal_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_subtotal {
  __typename: "TaxedMoney";
  gross: OrderLineAdd_draftOrderLineCreate_order_subtotal_gross;
}

export interface OrderLineAdd_draftOrderLineCreate_order_total_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_total_tax {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_total {
  __typename: "TaxedMoney";
  gross: OrderLineAdd_draftOrderLineCreate_order_total_gross;
  tax: OrderLineAdd_draftOrderLineCreate_order_total_tax;
}

export interface OrderLineAdd_draftOrderLineCreate_order_totalAuthorized {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_totalCaptured {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_user {
  __typename: "User";
  id: string;
  email: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order_availableShippingMethods {
  __typename: "ShippingMethod";
  id: string;
  name: string;
}

export interface OrderLineAdd_draftOrderLineCreate_order {
  __typename: "Order";
  id: string;
  billingAddress: OrderLineAdd_draftOrderLineCreate_order_billingAddress | null;
  created: any;
  events: (OrderLineAdd_draftOrderLineCreate_order_events | null)[] | null;
  fulfillments: (OrderLineAdd_draftOrderLineCreate_order_fulfillments | null)[];
  lines: (OrderLineAdd_draftOrderLineCreate_order_lines | null)[];
  number: string | null;
  paymentStatus: PaymentStatusEnum | null;
  shippingAddress: OrderLineAdd_draftOrderLineCreate_order_shippingAddress | null;
  shippingMethod: OrderLineAdd_draftOrderLineCreate_order_shippingMethod | null;
  shippingMethodName: string | null;
  shippingPrice: OrderLineAdd_draftOrderLineCreate_order_shippingPrice | null;
  status: OrderStatus;
  subtotal: OrderLineAdd_draftOrderLineCreate_order_subtotal | null;
  total: OrderLineAdd_draftOrderLineCreate_order_total | null;
  totalAuthorized: OrderLineAdd_draftOrderLineCreate_order_totalAuthorized | null;
  totalCaptured: OrderLineAdd_draftOrderLineCreate_order_totalCaptured | null;
  user: OrderLineAdd_draftOrderLineCreate_order_user | null;
  availableShippingMethods: (OrderLineAdd_draftOrderLineCreate_order_availableShippingMethods | null)[] | null;
}

export interface OrderLineAdd_draftOrderLineCreate {
  __typename: "DraftOrderLineCreate";
  errors: (OrderLineAdd_draftOrderLineCreate_errors | null)[] | null;
  order: OrderLineAdd_draftOrderLineCreate_order | null;
}

export interface OrderLineAdd {
  draftOrderLineCreate: OrderLineAdd_draftOrderLineCreate | null;
}

export interface OrderLineAddVariables {
  id: string;
  input: OrderLineCreateInput;
}
