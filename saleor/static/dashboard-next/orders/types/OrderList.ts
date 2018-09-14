/* tslint:disable */
// This file was automatically generated and should not be edited.

import { OrderStatus } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: OrderList
// ====================================================

export interface OrderList_orders_edges_node_total_gross {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface OrderList_orders_edges_node_total {
  __typename: "TaxedMoney";
  gross: OrderList_orders_edges_node_total_gross;
}

export interface OrderList_orders_edges_node {
  __typename: "Order";
  id: string;
  number: string | null;
  created: any;
  paymentStatus: string | null;
  status: OrderStatus;
  total: OrderList_orders_edges_node_total | null;
  userEmail: string;
}

export interface OrderList_orders_edges {
  __typename: "OrderCountableEdge";
  cursor: string;
  node: OrderList_orders_edges_node;
}

export interface OrderList_orders_pageInfo {
  __typename: "PageInfo";
  hasPreviousPage: boolean;
  hasNextPage: boolean;
  startCursor: string | null;
  endCursor: string | null;
}

export interface OrderList_orders {
  __typename: "OrderCountableConnection";
  edges: OrderList_orders_edges[];
  pageInfo: OrderList_orders_pageInfo;
}

export interface OrderList {
  orders: OrderList_orders | null;
}

export interface OrderListVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
