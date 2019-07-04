/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ListCustomers
// ====================================================

export interface ListCustomers_customers_edges_node_orders {
  __typename: "OrderCountableConnection";
  totalCount: number | null;
}

export interface ListCustomers_customers_edges_node {
  __typename: "User";
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  orders: ListCustomers_customers_edges_node_orders | null;
}

export interface ListCustomers_customers_edges {
  __typename: "UserCountableEdge";
  node: ListCustomers_customers_edges_node;
}

export interface ListCustomers_customers_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface ListCustomers_customers {
  __typename: "UserCountableConnection";
  edges: ListCustomers_customers_edges[];
  pageInfo: ListCustomers_customers_pageInfo;
}

export interface ListCustomers {
  customers: ListCustomers_customers | null;
}

export interface ListCustomersVariables {
  after?: string | null;
  before?: string | null;
  first?: number | null;
  last?: number | null;
}
