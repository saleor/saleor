/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchCategories
// ====================================================

export interface SearchCategories_categories_edges_node {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface SearchCategories_categories_edges {
  __typename: "CategoryCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SearchCategories_categories_edges_node;
}

export interface SearchCategories_categories {
  __typename: "CategoryCountableConnection";
  edges: SearchCategories_categories_edges[];
}

export interface SearchCategories {
  /**
   * List of the shop's categories.
   */
  categories: SearchCategories_categories | null;
}

export interface SearchCategoriesVariables {
  after?: string | null;
  first: number;
  query: string;
}
