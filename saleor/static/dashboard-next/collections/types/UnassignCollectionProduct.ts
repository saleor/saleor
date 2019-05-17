/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: UnassignCollectionProduct
// ====================================================

export interface UnassignCollectionProduct_collectionRemoveProducts_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node_productType {
  __typename: "ProductType";
  id: string;
  name: string;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node_thumbnail {
  __typename: "Image";
  url: string;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node {
  __typename: "Product";
  id: string;
  isPublished: boolean;
  name: string;
  productType: UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node_productType;
  thumbnail: UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node_thumbnail | null;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges {
  __typename: "ProductCountableEdge";
  node: UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges_node;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection_products {
  __typename: "ProductCountableConnection";
  edges: UnassignCollectionProduct_collectionRemoveProducts_collection_products_edges[];
  pageInfo: UnassignCollectionProduct_collectionRemoveProducts_collection_products_pageInfo;
}

export interface UnassignCollectionProduct_collectionRemoveProducts_collection {
  __typename: "Collection";
  id: string;
  products: UnassignCollectionProduct_collectionRemoveProducts_collection_products | null;
}

export interface UnassignCollectionProduct_collectionRemoveProducts {
  __typename: "CollectionRemoveProducts";
  errors: UnassignCollectionProduct_collectionRemoveProducts_errors[] | null;
  collection: UnassignCollectionProduct_collectionRemoveProducts_collection | null;
}

export interface UnassignCollectionProduct {
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
