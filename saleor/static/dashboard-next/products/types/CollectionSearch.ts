/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CollectionSearch
// ====================================================

export interface CollectionSearch_collections_edges_node {
  __typename: "Collection";
  id: string;
  name: string;
}

export interface CollectionSearch_collections_edges {
  __typename: "CollectionCountableEdge";
  node: CollectionSearch_collections_edges_node;
}

export interface CollectionSearch_collections {
  __typename: "CollectionCountableConnection";
  edges: CollectionSearch_collections_edges[];
}

export interface CollectionSearch {
  collections: CollectionSearch_collections | null;
}

export interface CollectionSearchVariables {
  query?: string | null;
}
