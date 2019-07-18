/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: UnassignCollectionProduct
// ====================================================

export interface UnassignCollectionProduct_collectionRemoveProducts_errors {
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

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  isPublished: boolean;
  name: string;
  productType: UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node_productType;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node_thumbnail | null;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products_pageInfo {
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

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products {
  __typename: "ProductCountableConnection";
  edges: UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: UnassignCollectionProduct_collectionRemoveProducts_collection_products_pageInfo;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of products in this collection.
   */
  products: UnassignCollectionProduct_collectionRemoveProducts_collection_products | null;
}

export interface UnassignCollectionProduct_collectionRemoveProducts {
  __typename: "CollectionRemoveProducts";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: UnassignCollectionProduct_collectionRemoveProducts_errors[] | null;
  /**
   * Collection from which products will be removed.
   */
  collection: UnassignCollectionProduct_collectionRemoveProducts_collection | null;
}

export interface UnassignCollectionProduct {
  /**
   * Remove products from a collection.
   */
  collectionRemoveProducts: UnassignCollectionProduct_collectionRemoveProducts | null;
}

export interface UnassignCollectionProductVariables {
  collectionId: string;
  productIds: (string | null)[];
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
