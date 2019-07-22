/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchCustomers
// ====================================================

export interface SearchCustomers_customers_edges_node {
  __typename: "User";
  id: string;
  email: string;
}

export interface SearchCustomers_customers_edges {
  __typename: "UserCountableEdge";
  node: SearchCustomers_customers_edges_node;
}

export interface SearchCustomers_customers {
  __typename: "UserCountableConnection";
  edges: SearchCustomers_customers_edges[];
}

export interface SearchCustomers {
  customers: SearchCustomers_customers | null;
}

export interface SearchCustomersVariables {
  after?: string | null;
  first: number;
  query: string;
}
