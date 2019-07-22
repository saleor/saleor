/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CollectionDetails
// ====================================================

export interface CollectionDetails_collection_backgroundImage {
  __typename: "Image";
  alt: string | null;
  url: string;
}

export interface CollectionDetails_collection_products_edges_node_productType {
  __typename: "ProductType";
  id: string;
  name: string;
}

export interface CollectionDetails_collection_products_edges_node_thumbnail {
  __typename: "Image";
  url: string;
}

export interface CollectionDetails_collection_products_edges_node {
  __typename: "Product";
  id: string;
  isPublished: boolean;
  name: string;
  productType: CollectionDetails_collection_products_edges_node_productType;
  thumbnail: CollectionDetails_collection_products_edges_node_thumbnail | null;
}

export interface CollectionDetails_collection_products_edges {
  __typename: "ProductCountableEdge";
  node: CollectionDetails_collection_products_edges_node;
}

export interface CollectionDetails_collection_products_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface CollectionDetails_collection_products {
  __typename: "ProductCountableConnection";
  edges: CollectionDetails_collection_products_edges[];
  pageInfo: CollectionDetails_collection_products_pageInfo;
}

export interface CollectionDetails_collection {
  __typename: "Collection";
  id: string;
  isPublished: boolean;
  name: string;
  backgroundImage: CollectionDetails_collection_backgroundImage | null;
  descriptionJson: any;
  publicationDate: any | null;
  seoDescription: string | null;
  seoTitle: string | null;
  products: CollectionDetails_collection_products | null;
}

export interface CollectionDetails_shop_homepageCollection {
  __typename: "Collection";
  id: string;
}

export interface CollectionDetails_shop {
  __typename: "Shop";
  homepageCollection: CollectionDetails_shop_homepageCollection | null;
}

export interface CollectionDetails {
  collection: CollectionDetails_collection | null;
  shop: CollectionDetails_shop | null;
}

export interface CollectionDetailsVariables {
  id: string;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
