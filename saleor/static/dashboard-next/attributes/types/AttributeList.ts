/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: AttributeList
// ====================================================

export interface AttributeList_attributes_edges_node_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface AttributeList_attributes_edges_node {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
  values: (AttributeList_attributes_edges_node_values | null)[] | null;
}

export interface AttributeList_attributes_edges {
  __typename: "AttributeCountableEdge";
  node: AttributeList_attributes_edges_node;
}

export interface AttributeList_attributes_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface AttributeList_attributes {
  __typename: "AttributeCountableConnection";
  edges: AttributeList_attributes_edges[];
  pageInfo: AttributeList_attributes_pageInfo;
}

export interface AttributeList {
  attributes: AttributeList_attributes | null;
}

export interface AttributeListVariables {
  query?: string | null;
  inCategory?: string | null;
  inCollection?: string | null;
  before?: string | null;
  after?: string | null;
  first?: number | null;
  last?: number | null;
}
