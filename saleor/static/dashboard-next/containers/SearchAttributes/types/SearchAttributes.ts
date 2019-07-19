/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchAttributes
// ====================================================

export interface SearchAttributes_attributes_edges_node {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface SearchAttributes_attributes_edges {
  __typename: "AttributeCountableEdge";
  node: SearchAttributes_attributes_edges_node;
}

export interface SearchAttributes_attributes_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface SearchAttributes_attributes {
  __typename: "AttributeCountableConnection";
  edges: SearchAttributes_attributes_edges[];
  pageInfo: SearchAttributes_attributes_pageInfo;
}

export interface SearchAttributes {
  attributes: SearchAttributes_attributes | null;
}

export interface SearchAttributesVariables {
  after?: string | null;
  first: number;
  query: string;
}
