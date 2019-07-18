/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CollectionAssignProduct
// ====================================================

export interface CollectionAssignProduct_collectionAddProducts_errors {
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

export interface CollectionAssignProduct_collectionAddProducts_collection_products_edges_node_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface CollectionAssignProduct_collectionAddProducts_collection_products_edges_node_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface CollectionAssignProduct_collectionAddProducts_collection_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  isPublished: boolean;
  name: string;
  productType: CollectionAssignProduct_collectionAddProducts_collection_products_edges_node_productType;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: CollectionAssignProduct_collectionAddProducts_collection_products_edges_node_thumbnail | null;
}

export interface CollectionAssignProduct_collectionAddProducts_collection_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: CollectionAssignProduct_collectionAddProducts_collection_products_edges_node;
}

export interface CollectionAssignProduct_collectionAddProducts_collection_products_pageInfo {
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

export interface CollectionAssignProduct_collectionAddProducts_collection_products {
  __typename: "ProductCountableConnection";
  edges: CollectionAssignProduct_collectionAddProducts_collection_products_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: CollectionAssignProduct_collectionAddProducts_collection_products_pageInfo;
}

export interface CollectionAssignProduct_collectionAddProducts_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * List of products in this collection.
   */
  products: CollectionAssignProduct_collectionAddProducts_collection_products | null;
}

export interface CollectionAssignProduct_collectionAddProducts {
  __typename: "CollectionAddProducts";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: CollectionAssignProduct_collectionAddProducts_errors[] | null;
  /**
   * Collection to which products will be added.
   */
  collection: CollectionAssignProduct_collectionAddProducts_collection | null;
}

export interface CollectionAssignProduct {
  /**
   * Adds products to a collection.
   */
  collectionAddProducts: CollectionAssignProduct_collectionAddProducts | null;
}

export interface CollectionAssignProductVariables {
  collectionId: string;
  productIds: string[];
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
