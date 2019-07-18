/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: RootCategories
// ====================================================

export interface RootCategories_categories_edges_node_children {
  __typename: "CategoryCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface RootCategories_categories_edges_node_products {
  __typename: "ProductCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface RootCategories_categories_edges_node {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * List of children of the category.
   */
  children: RootCategories_categories_edges_node_children | null;
  /**
   * List of products in the category.
   */
  products: RootCategories_categories_edges_node_products | null;
}

export interface RootCategories_categories_edges {
  __typename: "CategoryCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: RootCategories_categories_edges_node;
}

export interface RootCategories_categories_pageInfo {
  __typename: "PageInfo";
  /**
   * When paginating forwards, the cursor to continue.
   */
  endCursor: string | null;
  /**
   * When paginating forwards, are there more items?
   */
  hasNextPage: boolean;
  /**
   * When paginating backwards, are there more items?
   */
  hasPreviousPage: boolean;
  /**
   * When paginating backwards, the cursor to continue.
   */
  startCursor: string | null;
}

export interface RootCategories_categories {
  __typename: "CategoryCountableConnection";
  edges: RootCategories_categories_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: RootCategories_categories_pageInfo;
}

export interface RootCategories {
  /**
   * List of the shop's categories.
   */
  categories: RootCategories_categories | null;
}

export interface RootCategoriesVariables {
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
