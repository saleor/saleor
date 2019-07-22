/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { CatalogueInput, SaleType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: SaleCataloguesRemove
// ====================================================

export interface SaleCataloguesRemove_saleCataloguesRemove_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_products_edges_node_productType {
  __typename: "ProductType";
  id: string;
  name: string;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_products_edges_node_thumbnail {
  __typename: "Image";
  url: string;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_products_edges_node {
  __typename: "Product";
  id: string;
  name: string;
  isPublished: boolean;
  productType: SaleCataloguesRemove_saleCataloguesRemove_sale_products_edges_node_productType;
  thumbnail: SaleCataloguesRemove_saleCataloguesRemove_sale_products_edges_node_thumbnail | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_products_edges {
  __typename: "ProductCountableEdge";
  node: SaleCataloguesRemove_saleCataloguesRemove_sale_products_edges_node;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_products_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_products {
  __typename: "ProductCountableConnection";
  edges: SaleCataloguesRemove_saleCataloguesRemove_sale_products_edges[];
  pageInfo: SaleCataloguesRemove_saleCataloguesRemove_sale_products_pageInfo;
  totalCount: number | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_categories_edges_node_products {
  __typename: "ProductCountableConnection";
  totalCount: number | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_categories_edges_node {
  __typename: "Category";
  id: string;
  name: string;
  products: SaleCataloguesRemove_saleCataloguesRemove_sale_categories_edges_node_products | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_categories_edges {
  __typename: "CategoryCountableEdge";
  node: SaleCataloguesRemove_saleCataloguesRemove_sale_categories_edges_node;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_categories_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_categories {
  __typename: "CategoryCountableConnection";
  edges: SaleCataloguesRemove_saleCataloguesRemove_sale_categories_edges[];
  pageInfo: SaleCataloguesRemove_saleCataloguesRemove_sale_categories_pageInfo;
  totalCount: number | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_collections_edges_node_products {
  __typename: "ProductCountableConnection";
  totalCount: number | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_collections_edges_node {
  __typename: "Collection";
  id: string;
  name: string;
  products: SaleCataloguesRemove_saleCataloguesRemove_sale_collections_edges_node_products | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_collections_edges {
  __typename: "CollectionCountableEdge";
  node: SaleCataloguesRemove_saleCataloguesRemove_sale_collections_edges_node;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_collections_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale_collections {
  __typename: "CollectionCountableConnection";
  edges: SaleCataloguesRemove_saleCataloguesRemove_sale_collections_edges[];
  pageInfo: SaleCataloguesRemove_saleCataloguesRemove_sale_collections_pageInfo;
  totalCount: number | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove_sale {
  __typename: "Sale";
  id: string;
  name: string;
  type: SaleType;
  startDate: any;
  endDate: any | null;
  value: number;
  products: SaleCataloguesRemove_saleCataloguesRemove_sale_products | null;
  categories: SaleCataloguesRemove_saleCataloguesRemove_sale_categories | null;
  collections: SaleCataloguesRemove_saleCataloguesRemove_sale_collections | null;
}

export interface SaleCataloguesRemove_saleCataloguesRemove {
  __typename: "SaleRemoveCatalogues";
  errors: SaleCataloguesRemove_saleCataloguesRemove_errors[] | null;
  sale: SaleCataloguesRemove_saleCataloguesRemove_sale | null;
}

export interface SaleCataloguesRemove {
  saleCataloguesRemove: SaleCataloguesRemove_saleCataloguesRemove | null;
}

export interface SaleCataloguesRemoveVariables {
  input: CatalogueInput;
  id: string;
  after?: string | null;
  before?: string | null;
  first?: number | null;
  last?: number | null;
}
