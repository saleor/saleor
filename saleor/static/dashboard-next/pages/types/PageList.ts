/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PageList
// ====================================================

export interface PageList_pages_edges_node {
  __typename: "Page";
  id: string;
  title: string;
  slug: string;
  isVisible: boolean | null;
}

export interface PageList_pages_edges {
  __typename: "PageCountableEdge";
  node: PageList_pages_edges_node;
}

export interface PageList_pages_pageInfo {
  __typename: "PageInfo";
  hasPreviousPage: boolean;
  hasNextPage: boolean;
  startCursor: string | null;
  endCursor: string | null;
}

export interface PageList_pages {
  __typename: "PageCountableConnection";
  edges: PageList_pages_edges[];
  pageInfo: PageList_pages_pageInfo;
}

export interface PageList {
  pages: PageList_pages | null;
}

export interface PageListVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
