/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CategorySearch
// ====================================================

export interface CategorySearch_categories_edges_node {
  __typename: "Category";
  id: string;
  name: string;
}

export interface CategorySearch_categories_edges {
  __typename: "CategoryCountableEdge";
  node: CategorySearch_categories_edges_node;
}

export interface CategorySearch_categories {
  __typename: "CategoryCountableConnection";
  edges: CategorySearch_categories_edges[];
}

export interface CategorySearch {
  categories: CategorySearch_categories | null;
}

export interface CategorySearchVariables {
  query?: string | null;
}
