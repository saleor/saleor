/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchAttributes
// ====================================================

export interface SearchAttributes_productType_availableAttributes_edges_node {
  __typename: "Attribute";
  id: string;
  name: string | null;
  slug: string | null;
}

export interface SearchAttributes_productType_availableAttributes_edges {
  __typename: "AttributeCountableEdge";
  node: SearchAttributes_productType_availableAttributes_edges_node;
}

export interface SearchAttributes_productType_availableAttributes_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface SearchAttributes_productType_availableAttributes {
  __typename: "AttributeCountableConnection";
  edges: SearchAttributes_productType_availableAttributes_edges[];
  pageInfo: SearchAttributes_productType_availableAttributes_pageInfo;
}

export interface SearchAttributes_productType {
  __typename: "ProductType";
  id: string;
  availableAttributes: SearchAttributes_productType_availableAttributes | null;
}

export interface SearchAttributes {
  productType: SearchAttributes_productType | null;
}

export interface SearchAttributesVariables {
  id: string;
  after?: string | null;
  first: number;
  query: string;
}
