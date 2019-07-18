/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: PageList
// ====================================================

export interface PageList_pages_edges_node {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  title: string;
  slug: string;
  isPublished: boolean;
}

export interface PageList_pages_edges {
  __typename: "PageCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: PageList_pages_edges_node;
}

export interface PageList_pages_pageInfo {
  __typename: "PageInfo";
  /**
   * When paginating backwards, are there more items?
   */
  hasPreviousPage: boolean;
  /**
   * When paginating forwards, are there more items?
   */
  hasNextPage: boolean;
  /**
   * When paginating backwards, the cursor to continue.
   */
  startCursor: string | null;
  /**
   * When paginating forwards, the cursor to continue.
   */
  endCursor: string | null;
}

export interface PageList_pages {
  __typename: "PageCountableConnection";
  edges: PageList_pages_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: PageList_pages_pageInfo;
}

export interface PageList {
  /**
   * List of the shop's pages.
   */
  pages: PageList_pages | null;
}

export interface PageListVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
