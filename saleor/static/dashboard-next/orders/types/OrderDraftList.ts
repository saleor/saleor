/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { PaymentChargeStatusEnum, OrderStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: OrderDraftList
// ====================================================

export interface OrderDraftList_draftOrders_edges_node_billingAddress_country {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface OrderDraftList_draftOrders_edges_node_billingAddress {
  __typename: "Address";
  city: string;
  cityArea: string;
  companyName: string;
  country: OrderDraftList_draftOrders_edges_node_billingAddress_country;
  countryArea: string;
  firstName: string;
  id: string;
  lastName: string;
  phone: string | null;
  postalCode: string;
  streetAddress1: string;
  streetAddress2: string;
}

export interface OrderDraftList_draftOrders_edges_node_total_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderDraftList_draftOrders_edges_node_total {
  __typename: "TaxedMoney";
  gross: OrderDraftList_draftOrders_edges_node_total_gross;
}

export interface OrderDraftList_draftOrders_edges_node {
  __typename: "Order";
  billingAddress: OrderDraftList_draftOrders_edges_node_billingAddress | null;
  created: any;
  id: string;
  number: string | null;
  paymentStatus: PaymentChargeStatusEnum | null;
  status: OrderStatus;
  total: OrderDraftList_draftOrders_edges_node_total | null;
  userEmail: string | null;
}

export interface OrderDraftList_draftOrders_edges {
  __typename: "OrderCountableEdge";
  node: OrderDraftList_draftOrders_edges_node;
}

export interface OrderDraftList_draftOrders_pageInfo {
  __typename: "PageInfo";
  hasPreviousPage: boolean;
  hasNextPage: boolean;
  startCursor: string | null;
  endCursor: string | null;
}

export interface OrderDraftList_draftOrders {
  __typename: "OrderCountableConnection";
  edges: OrderDraftList_draftOrders_edges[];
  pageInfo: OrderDraftList_draftOrders_pageInfo;
}

export interface OrderDraftList {
  draftOrders: OrderDraftList_draftOrders | null;
}

export interface OrderDraftListVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
