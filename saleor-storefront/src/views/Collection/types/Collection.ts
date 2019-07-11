/* tslint:disable */
// This file was automatically generated and should not be edited.

import { ProductOrder } from "./../../../../types/globalTypes";

// ====================================================
// GraphQL query operation: Collection
// ====================================================

export interface Collection_collection_backgroundImage {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface Collection_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  slug: string;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
  backgroundImage: Collection_collection_backgroundImage | null;
}

export interface Collection_products_edges_node_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
  /**
   * Alt text for an image.
   */
  alt: string | null;
}

export interface Collection_products_edges_node_thumbnail2x {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface Collection_products_edges_node_price {
  __typename: "Money";
  /**
   * Amount of money.
   */
  amount: number;
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Money formatted according to the current locale.
   */
  localized: string;
}

export interface Collection_products_edges_node_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface Collection_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: Collection_products_edges_node_thumbnail | null;
  /**
   * The main thumbnail for a product.
   */
  thumbnail2x: Collection_products_edges_node_thumbnail2x | null;
  /**
   * The product's default base price.
   */
  price: Collection_products_edges_node_price | null;
  category: Collection_products_edges_node_category;
}

export interface Collection_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: Collection_products_edges_node;
}

export interface Collection_products_pageInfo {
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

export interface Collection_products {
  __typename: "ProductCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
  edges: Collection_products_edges[];
  pageInfo: Collection_products_pageInfo;
}

export interface Collection_attributes_edges_node_values {
  __typename: "AttributeValue";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of a value displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of a value (unique per attribute).
   */
  slug: string | null;
}

export interface Collection_attributes_edges_node {
  __typename: "Attribute";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of an attribute displayed in the interface.
   */
  name: string | null;
  /**
   * Internal representation of an attribute name.
   */
  slug: string | null;
  /**
   * List of attribute's values.
   */
  values: (Collection_attributes_edges_node_values | null)[] | null;
}

export interface Collection_attributes_edges {
  __typename: "AttributeCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: Collection_attributes_edges_node;
}

export interface Collection_attributes {
  __typename: "AttributeCountableConnection";
  edges: Collection_attributes_edges[];
}

export interface Collection {
  /**
   * Lookup a collection by ID.
   */
  collection: Collection_collection | null;
  /**
   * List of the shop's products.
   */
  products: Collection_products | null;
  /**
   * List of the shop's attributes.
   */
  attributes: Collection_attributes | null;
}

export interface CollectionVariables {
  id: string;
  attributes?: (any | null)[] | null;
  after?: string | null;
  pageSize?: number | null;
  sortBy?: ProductOrder | null;
  priceLte?: number | null;
  priceGte?: number | null;
}
