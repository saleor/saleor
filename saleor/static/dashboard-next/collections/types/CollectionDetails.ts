/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CollectionDetails
// ====================================================

export interface CollectionDetails_collection_backgroundImage {
  __typename: "Image";
  /**
   * Alt text for an image.
   */
  alt: string | null;
  /**
   * The URL of the image.
   */
  url: string;
}

export interface CollectionDetails_collection_products_edges_node_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface CollectionDetails_collection_products_edges_node_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface CollectionDetails_collection_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  isPublished: boolean;
  name: string;
  productType: CollectionDetails_collection_products_edges_node_productType;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: CollectionDetails_collection_products_edges_node_thumbnail | null;
}

export interface CollectionDetails_collection_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: CollectionDetails_collection_products_edges_node;
}

export interface CollectionDetails_collection_products_pageInfo {
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

export interface CollectionDetails_collection_products {
  __typename: "ProductCountableConnection";
  edges: CollectionDetails_collection_products_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: CollectionDetails_collection_products_pageInfo;
}

export interface CollectionDetails_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  isPublished: boolean;
  name: string;
  backgroundImage: CollectionDetails_collection_backgroundImage | null;
  descriptionJson: any;
  publicationDate: any | null;
  seoDescription: string | null;
  seoTitle: string | null;
  /**
   * List of products in this collection.
   */
  products: CollectionDetails_collection_products | null;
}

export interface CollectionDetails_shop_homepageCollection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
}

export interface CollectionDetails_shop {
  __typename: "Shop";
  /**
   * Collection displayed on homepage
   */
  homepageCollection: CollectionDetails_shop_homepageCollection | null;
}

export interface CollectionDetails {
  /**
   * Lookup a collection by ID.
   */
  collection: CollectionDetails_collection | null;
  /**
   * Represents a shop resources.
   */
  shop: CollectionDetails_shop | null;
}

export interface CollectionDetailsVariables {
  id: string;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
