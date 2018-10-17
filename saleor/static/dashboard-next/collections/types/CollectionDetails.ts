/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CollectionDetails
// ====================================================

export interface CollectionDetails_collection_backgroundImage {
  __typename: "Image";
  url: string;
}

export interface CollectionDetails_collection_products_edges_node_productType {
  __typename: "ProductType";
  id: string;
  name: string;
}

export interface CollectionDetails_collection_products_edges_node {
  __typename: "Product";
  id: string;
  isPublished: boolean;
  name: string;
  productType: CollectionDetails_collection_products_edges_node_productType;
  thumbnailUrl: string | null;
}

export interface CollectionDetails_collection_products_edges {
  __typename: "ProductCountableEdge";
  cursor: string;
  node: CollectionDetails_collection_products_edges_node;
}

export interface CollectionDetails_collection_products {
  __typename: "ProductCountableConnection";
  edges: CollectionDetails_collection_products_edges[];
}

export interface CollectionDetails_collection {
  __typename: "Collection";
  backgroundImage: CollectionDetails_collection_backgroundImage | null;
  seoDescription: string | null;
  seoTitle: string | null;
  isPublished: boolean;
  products: CollectionDetails_collection_products | null;
}

export interface CollectionDetails {
  collection: CollectionDetails_collection | null;
}

export interface CollectionDetailsVariables {
  id: string;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
