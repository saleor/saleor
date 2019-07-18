/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { SaleType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: SaleDetailsFragment
// ====================================================

export interface SaleDetailsFragment_products_edges_node_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SaleDetailsFragment_products_edges_node_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface SaleDetailsFragment_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  isPublished: boolean;
  productType: SaleDetailsFragment_products_edges_node_productType;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: SaleDetailsFragment_products_edges_node_thumbnail | null;
}

export interface SaleDetailsFragment_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SaleDetailsFragment_products_edges_node;
}

export interface SaleDetailsFragment_products_pageInfo {
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

export interface SaleDetailsFragment_products {
  __typename: "ProductCountableConnection";
  edges: SaleDetailsFragment_products_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: SaleDetailsFragment_products_pageInfo;
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleDetailsFragment_categories_edges_node_products {
  __typename: "ProductCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleDetailsFragment_categories_edges_node {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * List of products in the category.
   */
  products: SaleDetailsFragment_categories_edges_node_products | null;
}

export interface SaleDetailsFragment_categories_edges {
  __typename: "CategoryCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SaleDetailsFragment_categories_edges_node;
}

export interface SaleDetailsFragment_categories_pageInfo {
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

export interface SaleDetailsFragment_categories {
  __typename: "CategoryCountableConnection";
  edges: SaleDetailsFragment_categories_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: SaleDetailsFragment_categories_pageInfo;
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleDetailsFragment_collections_edges_node_products {
  __typename: "ProductCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleDetailsFragment_collections_edges_node {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * List of products in this collection.
   */
  products: SaleDetailsFragment_collections_edges_node_products | null;
}

export interface SaleDetailsFragment_collections_edges {
  __typename: "CollectionCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SaleDetailsFragment_collections_edges_node;
}

export interface SaleDetailsFragment_collections_pageInfo {
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

export interface SaleDetailsFragment_collections {
  __typename: "CollectionCountableConnection";
  edges: SaleDetailsFragment_collections_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: SaleDetailsFragment_collections_pageInfo;
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface SaleDetailsFragment {
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
  products: SaleDetailsFragment_products | null;
  /**
   * List of categories this sale applies to.
   */
  categories: SaleDetailsFragment_categories | null;
  /**
   * List of collections this sale applies to.
   */
  collections: SaleDetailsFragment_collections | null;
}
