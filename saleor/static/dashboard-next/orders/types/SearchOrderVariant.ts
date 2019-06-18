/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchOrderVariant
// ====================================================

export interface SearchOrderVariant_products_edges_node_thumbnail {
  __typename: "Image";
  url: string;
}

export interface SearchOrderVariant_products_edges_node_variants_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface SearchOrderVariant_products_edges_node_variants {
  __typename: "ProductVariant";
  id: string;
  name: string;
  sku: string;
  price: SearchOrderVariant_products_edges_node_variants_price | null;
}

export interface SearchOrderVariant_products_edges_node {
  __typename: "Product";
  id: string;
  name: string;
  thumbnail: SearchOrderVariant_products_edges_node_thumbnail | null;
  variants: (SearchOrderVariant_products_edges_node_variants | null)[] | null;
}

export interface SearchOrderVariant_products_edges {
  __typename: "ProductCountableEdge";
  node: SearchOrderVariant_products_edges_node;
}

export interface SearchOrderVariant_products_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface SearchOrderVariant_products {
  __typename: "ProductCountableConnection";
  edges: SearchOrderVariant_products_edges[];
  pageInfo: SearchOrderVariant_products_pageInfo;
}

export interface SearchOrderVariant {
  products: SearchOrderVariant_products | null;
}

export interface SearchOrderVariantVariables {
  first: number;
  query: string;
  after?: string | null;
}
