/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CollectionList
// ====================================================

export interface CollectionList_collections_edges_node_products {
  __typename: "ProductCountableConnection";
  totalCount: number | null;
}

export interface CollectionList_collections_edges_node {
  __typename: "Collection";
  id: string;
  isPublished: boolean;
  name: string;
  products: CollectionList_collections_edges_node_products | null;
}

export interface CollectionList_collections_edges {
  __typename: "CollectionCountableEdge";
  node: CollectionList_collections_edges_node;
}

export interface CollectionList_collections {
  __typename: "CollectionCountableConnection";
  edges: CollectionList_collections_edges[];
}

export interface CollectionList {
  collections: CollectionList_collections | null;
}

export interface CollectionListVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
