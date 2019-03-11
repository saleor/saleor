/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: UserSearch
// ====================================================

export interface UserSearch_customers_edges_node {
  __typename: "User";
  id: string;
  email: string;
}

export interface UserSearch_customers_edges {
  __typename: "UserCountableEdge";
  node: UserSearch_customers_edges_node;
}

export interface UserSearch_customers {
  __typename: "UserCountableConnection";
  edges: UserSearch_customers_edges[];
}

export interface UserSearch {
  customers: UserSearch_customers | null;
}

export interface UserSearchVariables {
  search: string;
}
