/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductTypeList
// ====================================================

export interface ProductTypeList_productTypes_edges_node_taxType {
  __typename: "TaxType";
  description: string | null;
  taxCode: string | null;
}

export interface ProductTypeList_productTypes_edges_node {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  isShippingRequired: boolean;
  taxType: ProductTypeList_productTypes_edges_node_taxType | null;
}

export interface ProductTypeList_productTypes_edges {
  __typename: "ProductTypeCountableEdge";
  node: ProductTypeList_productTypes_edges_node;
}

export interface ProductTypeList_productTypes_pageInfo {
  __typename: "PageInfo";
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
  endCursor: string | null;
}

export interface ProductTypeList_productTypes {
  __typename: "ProductTypeCountableConnection";
  edges: ProductTypeList_productTypes_edges[];
  pageInfo: ProductTypeList_productTypes_pageInfo;
}

export interface ProductTypeList {
  productTypes: ProductTypeList_productTypes | null;
}

export interface ProductTypeListVariables {
  after?: string | null;
  before?: string | null;
  first?: number | null;
  last?: number | null;
}
