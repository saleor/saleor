/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { CatalogueInput, SaleType } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: SaleCataloguesAdd
// ====================================================

export interface SaleCataloguesAdd_saleCataloguesAdd_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_products_edges_node_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_products_edges_node_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  isPublished: boolean;
  productType: SaleCataloguesAdd_saleCataloguesAdd_sale_products_edges_node_productType;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: SaleCataloguesAdd_saleCataloguesAdd_sale_products_edges_node_thumbnail | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SaleCataloguesAdd_saleCataloguesAdd_sale_products_edges_node;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_products_pageInfo {
  __typename: "PageInfo";
  /**
   * When paginating forwards, the cursor to continue.
   */
  endCursor: string | null;
  /**
   * When paginating forwards, are there more items?
   */
  hasNextPage: boolean;
  /**
   * When paginating backwards, are there more items?
   */
  hasPreviousPage: boolean;
  /**
   * When paginating backwards, the cursor to continue.
   */
  startCursor: string | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_products {
  __typename: "ProductCountableConnection";
  edges: SaleCataloguesAdd_saleCataloguesAdd_sale_products_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: SaleCataloguesAdd_saleCataloguesAdd_sale_products_pageInfo;
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_categories_edges_node_products {
  __typename: "ProductCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_categories_edges_node {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * List of products in the category.
   */
  products: SaleCataloguesAdd_saleCataloguesAdd_sale_categories_edges_node_products | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_categories_edges {
  __typename: "CategoryCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SaleCataloguesAdd_saleCataloguesAdd_sale_categories_edges_node;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_categories_pageInfo {
  __typename: "PageInfo";
  /**
   * When paginating forwards, the cursor to continue.
   */
  endCursor: string | null;
  /**
   * When paginating forwards, are there more items?
   */
  hasNextPage: boolean;
  /**
   * When paginating backwards, are there more items?
   */
  hasPreviousPage: boolean;
  /**
   * When paginating backwards, the cursor to continue.
   */
  startCursor: string | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_categories {
  __typename: "CategoryCountableConnection";
  edges: SaleCataloguesAdd_saleCataloguesAdd_sale_categories_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: SaleCataloguesAdd_saleCataloguesAdd_sale_categories_pageInfo;
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_collections_edges_node_products {
  __typename: "ProductCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_collections_edges_node {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * List of products in this collection.
   */
  products: SaleCataloguesAdd_saleCataloguesAdd_sale_collections_edges_node_products | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_collections_edges {
  __typename: "CollectionCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SaleCataloguesAdd_saleCataloguesAdd_sale_collections_edges_node;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_collections_pageInfo {
  __typename: "PageInfo";
  /**
   * When paginating forwards, the cursor to continue.
   */
  endCursor: string | null;
  /**
   * When paginating forwards, are there more items?
   */
  hasNextPage: boolean;
  /**
   * When paginating backwards, are there more items?
   */
  hasPreviousPage: boolean;
  /**
   * When paginating backwards, the cursor to continue.
   */
  startCursor: string | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale_collections {
  __typename: "CollectionCountableConnection";
  edges: SaleCataloguesAdd_saleCataloguesAdd_sale_collections_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: SaleCataloguesAdd_saleCataloguesAdd_sale_collections_pageInfo;
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd_sale {
  __typename: "Sale";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  type: SaleType;
  startDate: any;
  endDate: any | null;
  value: number;
  /**
   * List of products this sale applies to.
   */
  products: SaleCataloguesAdd_saleCataloguesAdd_sale_products | null;
  /**
   * List of categories this sale applies to.
   */
  categories: SaleCataloguesAdd_saleCataloguesAdd_sale_categories | null;
  /**
   * List of collections this sale applies to.
   */
  collections: SaleCataloguesAdd_saleCataloguesAdd_sale_collections | null;
}

export interface SaleCataloguesAdd_saleCataloguesAdd {
  __typename: "SaleAddCatalogues";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: SaleCataloguesAdd_saleCataloguesAdd_errors[] | null;
  /**
   * Sale of which catalogue IDs will be modified.
   */
  sale: SaleCataloguesAdd_saleCataloguesAdd_sale | null;
}

export interface SaleCataloguesAdd {
  /**
   * Adds products, categories, collections to a voucher.
   */
  saleCataloguesAdd: SaleCataloguesAdd_saleCataloguesAdd | null;
}

export interface SaleCataloguesAddVariables {
  input: CatalogueInput;
  id: string;
  after?: string | null;
  before?: string | null;
  first?: number | null;
  last?: number | null;
}
