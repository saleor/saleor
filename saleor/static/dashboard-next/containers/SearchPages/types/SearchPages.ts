/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchPages
// ====================================================

export interface SearchPages_pages_edges_node {
  __typename: "Page";
  id: string;
  title: string;
}

export interface SearchPages_pages_edges {
  __typename: "PageCountableEdge";
  node: SearchPages_pages_edges_node;
}

export interface SearchPages_pages {
  __typename: "PageCountableConnection";
  edges: SearchPages_pages_edges[];
}

export interface SearchPages {
  pages: SearchPages_pages | null;
}

export interface SearchPagesVariables {
  after?: string | null;
  first: number;
  query: string;
}
