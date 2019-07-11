/* tslint:disable */
// This file was automatically generated and should not be edited.

import { ProductOrder } from "./../../../../types/globalTypes";

// ====================================================
// GraphQL query operation: SearchProducts
// ====================================================

export interface SearchProducts_products_edges_node_thumbnail {
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

export interface SearchProducts_products_edges_node_thumbnail2x {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface SearchProducts_products_edges_node_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SearchProducts_products_edges_node_price {
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

export interface SearchProducts_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: SearchProducts_products_edges_node_thumbnail | null;
  /**
   * The main thumbnail for a product.
   */
  thumbnail2x: SearchProducts_products_edges_node_thumbnail2x | null;
  category: SearchProducts_products_edges_node_category;
  /**
   * The product's default base price.
   */
  price: SearchProducts_products_edges_node_price | null;
}

export interface SearchProducts_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SearchProducts_products_edges_node;
}

export interface SearchProducts_products_pageInfo {
  __typename: "PageInfo";
  /**
   * When paginating forwards, the cursor to continue.
   */
  endCursor: string | null;
  /**
   * When paginating forwards, are there more items?
   */
  hasNextPage: boolean;
}

export interface SearchProducts_products {
  __typename: "ProductCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
  edges: SearchProducts_products_edges[];
  pageInfo: SearchProducts_products_pageInfo;
}

export interface SearchProducts_attributes_edges_node_values {
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

export interface SearchProducts_attributes_edges_node {
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
  values: (SearchProducts_attributes_edges_node_values | null)[] | null;
}

export interface SearchProducts_attributes_edges {
  __typename: "AttributeCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SearchProducts_attributes_edges_node;
}

export interface SearchProducts_attributes {
  __typename: "AttributeCountableConnection";
  edges: SearchProducts_attributes_edges[];
}

export interface SearchProducts {
  /**
   * List of the shop's products.
   */
  products: SearchProducts_products | null;
  /**
   * List of the shop's attributes.
   */
  attributes: SearchProducts_attributes | null;
}

export interface SearchProductsVariables {
  query: string;
  attributes?: (any | null)[] | null;
  pageSize?: number | null;
  sortBy?: ProductOrder | null;
  after?: string | null;
}
