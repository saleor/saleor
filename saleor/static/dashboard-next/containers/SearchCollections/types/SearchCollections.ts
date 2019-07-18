/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchCollections
// ====================================================

export interface SearchCollections_collections_edges_node {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SearchCollections_collections_edges {
  __typename: "CollectionCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SearchCollections_collections_edges_node;
}

export interface SearchCollections_collections {
  __typename: "CollectionCountableConnection";
  edges: SearchCollections_collections_edges[];
}

export interface SearchCollections {
  /**
   * List of the shop's collections.
   */
  collections: SearchCollections_collections | null;
}

export interface SearchCollectionsVariables {
  after?: string | null;
  first: number;
  query: string;
}
