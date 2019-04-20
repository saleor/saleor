/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: SearchCategories
// ====================================================

export interface SearchCategories_categories_edges_node {
  __typename: "Category";
  id: string;
  name: string;
}

export interface SearchCategories_categories_edges {
  __typename: "CategoryCountableEdge";
  node: SearchCategories_categories_edges_node;
}

export interface SearchCategories_categories {
  __typename: "CategoryCountableConnection";
  edges: SearchCategories_categories_edges[];
}

export interface SearchCategories {
  categories: SearchCategories_categories | null;
}

export interface SearchCategoriesVariables {
  query: string;
}
