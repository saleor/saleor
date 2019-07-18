/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchCustomers
// ====================================================

export interface SearchCustomers_customers_edges_node {
  __typename: "User";
  /**
   * The ID of the object.
   */
  id: string;
  email: string;
}

export interface SearchCustomers_customers_edges {
  __typename: "UserCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SearchCustomers_customers_edges_node;
}

export interface SearchCustomers_customers {
  __typename: "UserCountableConnection";
  edges: SearchCustomers_customers_edges[];
}

export interface SearchCustomers {
  /**
   * List of the shop's customers.
   */
  customers: SearchCustomers_customers | null;
}

export interface SearchCustomersVariables {
  after?: string | null;
  first: number;
  query: string;
}
