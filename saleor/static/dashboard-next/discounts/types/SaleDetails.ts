/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { SaleType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SaleDetails
// ====================================================

export interface SaleDetails_sale_products_edges_node_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SaleDetails_sale_products_edges_node_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface SaleDetails_sale_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  isPublished: boolean;
  productType: SaleDetails_sale_products_edges_node_productType;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: SaleDetails_sale_products_edges_node_thumbnail | null;
}

export interface SaleDetails_sale_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SaleDetails_sale_products_edges_node;
}

export interface SaleDetails_sale_products_pageInfo {
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

export interface SaleDetails_sale_products {
  __typename: "ProductCountableConnection";
  edges: SaleDetails_sale_products_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: SaleDetails_sale_products_pageInfo;
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleDetails_sale_categories_edges_node_products {
  __typename: "ProductCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleDetails_sale_categories_edges_node {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * List of products in the category.
   */
  products: SaleDetails_sale_categories_edges_node_products | null;
}

export interface SaleDetails_sale_categories_edges {
  __typename: "CategoryCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SaleDetails_sale_categories_edges_node;
}

export interface SaleDetails_sale_categories_pageInfo {
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

export interface SaleDetails_sale_categories {
  __typename: "CategoryCountableConnection";
  edges: SaleDetails_sale_categories_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: SaleDetails_sale_categories_pageInfo;
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleDetails_sale_collections_edges_node_products {
  __typename: "ProductCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleDetails_sale_collections_edges_node {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * List of products in this collection.
   */
  products: SaleDetails_sale_collections_edges_node_products | null;
}

export interface SaleDetails_sale_collections_edges {
  __typename: "CollectionCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SaleDetails_sale_collections_edges_node;
}

export interface SaleDetails_sale_collections_pageInfo {
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

export interface SaleDetails_sale_collections {
  __typename: "CollectionCountableConnection";
  edges: SaleDetails_sale_collections_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: SaleDetails_sale_collections_pageInfo;
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleDetails_sale {
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
  products: SaleDetails_sale_products | null;
  /**
   * List of categories this sale applies to.
   */
  categories: SaleDetails_sale_categories | null;
  /**
   * List of collections this sale applies to.
   */
  collections: SaleDetails_sale_collections | null;
}

export interface SaleDetails {
  /**
   * Lookup a sale by ID.
   */
  sale: SaleDetails_sale | null;
}

export interface SaleDetailsVariables {
  id: string;
  after?: string | null;
  before?: string | null;
  first?: number | null;
  last?: number | null;
}
