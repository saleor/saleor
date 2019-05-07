/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchCollections
// ====================================================

export interface SearchCollections_collections_edges_node {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface SearchCollections_collections_edges {
  __typename: "CollectionCountableEdge";
  node: SearchCollections_collections_edges_node;
}

export interface SearchCollections_collections {
  __typename: "CollectionCountableConnection";
  edges: SearchCollections_collections_edges[];
}

export interface SearchCollections {
  collections: SearchCollections_collections | null;
}

export interface SearchCollectionsVariables {
  query: string;
}
