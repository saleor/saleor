/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CollectionAssignProduct
// ====================================================

export interface CollectionAssignProduct_collectionAddProducts_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CollectionAssignProduct_collectionAddProducts_collection_products_edges_node_productType {
  __typename: "ProductType";
  id: string;
  name: string;
}

export interface CollectionAssignProduct_collectionAddProducts_collection_products_edges_node_thumbnail {
  __typename: "Image";
  url: string;
}

export interface CollectionAssignProduct_collectionAddProducts_collection_products_edges_node {
  __typename: "Product";
  id: string;
  isPublished: boolean;
  name: string;
  productType: CollectionAssignProduct_collectionAddProducts_collection_products_edges_node_productType;
  thumbnail: CollectionAssignProduct_collectionAddProducts_collection_products_edges_node_thumbnail | null;
}

export interface CollectionAssignProduct_collectionAddProducts_collection_products_edges {
  __typename: "ProductCountableEdge";
  node: CollectionAssignProduct_collectionAddProducts_collection_products_edges_node;
}

export interface CollectionAssignProduct_collectionAddProducts_collection_products_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface CollectionAssignProduct_collectionAddProducts_collection_products {
  __typename: "ProductCountableConnection";
  edges: CollectionAssignProduct_collectionAddProducts_collection_products_edges[];
  pageInfo: CollectionAssignProduct_collectionAddProducts_collection_products_pageInfo;
}

export interface CollectionAssignProduct_collectionAddProducts_collection {
  __typename: "Collection";
  id: string;
  products: CollectionAssignProduct_collectionAddProducts_collection_products | null;
}

export interface CollectionAssignProduct_collectionAddProducts {
  __typename: "CollectionAddProducts";
  errors: CollectionAssignProduct_collectionAddProducts_errors[] | null;
  collection: CollectionAssignProduct_collectionAddProducts_collection | null;
}

export interface CollectionAssignProduct {
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
