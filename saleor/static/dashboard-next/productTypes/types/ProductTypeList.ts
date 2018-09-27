/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: ProductTypeList
// ====================================================

export interface ProductTypeList_productTypes_edges_node_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
}

export interface ProductTypeList_productTypes_edges_node_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
}

export interface ProductTypeList_productTypes_edges_node {
  __typename: "ProductType";
  id: string;
  name: string;
  hasVariants: boolean;
  productAttributes: (ProductTypeList_productTypes_edges_node_productAttributes | null)[] | null;
  variantAttributes: (ProductTypeList_productTypes_edges_node_variantAttributes | null)[] | null;
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
