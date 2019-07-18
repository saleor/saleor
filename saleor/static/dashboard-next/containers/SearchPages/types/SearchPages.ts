/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchPages
// ====================================================

export interface SearchPages_pages_edges_node {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
}

export interface SearchPages_pages_edges {
  __typename: "PageCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SearchPages_pages_edges_node;
}

export interface SearchPages_pages {
  __typename: "PageCountableConnection";
  edges: SearchPages_pages_edges[];
}

export interface SearchPages {
  /**
   * List of the shop's pages.
   */
  pages: SearchPages_pages | null;
}

export interface SearchPagesVariables {
  after?: string | null;
  first: number;
  query: string;
}
