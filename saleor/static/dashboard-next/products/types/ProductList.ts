/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { StockAvailability } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductList
// ====================================================

export interface ProductList_products_edges_node_thumbnail {
  __typename: "Image";
  url: string;
}

export interface ProductList_products_edges_node_availability {
  __typename: "ProductAvailability";
  available: boolean | null;
}

export interface ProductList_products_edges_node_price {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface ProductList_products_edges_node_productType {
  __typename: "ProductType";
  id: string;
  name: string;
}

export interface ProductList_products_edges_node {
  __typename: "Product";
  id: string;
  name: string;
  thumbnail: ProductList_products_edges_node_thumbnail | null;
  availability: ProductList_products_edges_node_availability | null;
  price: ProductList_products_edges_node_price | null;
  productType: ProductList_products_edges_node_productType;
}

export interface ProductList_products_edges {
  __typename: "ProductCountableEdge";
  node: ProductList_products_edges_node;
}

export interface ProductList_products_pageInfo {
  __typename: "PageInfo";
  hasPreviousPage: boolean;
  hasNextPage: boolean;
  startCursor: string | null;
  endCursor: string | null;
}

export interface ProductList_products {
  __typename: "ProductCountableConnection";
  edges: ProductList_products_edges[];
  pageInfo: ProductList_products_pageInfo;
}

export interface ProductList {
  products: ProductList_products | null;
}

export interface ProductListVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
  stockAvailability?: StockAvailability | null;
}
