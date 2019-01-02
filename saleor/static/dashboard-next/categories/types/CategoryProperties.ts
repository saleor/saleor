/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CategoryProperties
// ====================================================

export interface CategoryProperties_category_parent {
  __typename: "Category";
  id: string;
}

export interface CategoryProperties_category_children_edges_node_children {
  __typename: "CategoryCountableConnection";
  totalCount: number | null;
}

export interface CategoryProperties_category_children_edges_node_products {
  __typename: "ProductCountableConnection";
  totalCount: number | null;
}

export interface CategoryProperties_category_children_edges_node {
  __typename: "Category";
  id: string;
  name: string;
  children: CategoryProperties_category_children_edges_node_children | null;
  products: CategoryProperties_category_children_edges_node_products | null;
}

export interface CategoryProperties_category_children_edges {
  __typename: "CategoryCountableEdge";
  node: CategoryProperties_category_children_edges_node;
}

export interface CategoryProperties_category_children {
  __typename: "CategoryCountableConnection";
  edges: CategoryProperties_category_children_edges[];
}

export interface CategoryProperties_category_products_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface CategoryProperties_category_products_edges_node_productType {
  __typename: "ProductType";
  id: string;
  name: string;
}

export interface CategoryProperties_category_products_edges_node {
  __typename: "Product";
  id: string;
  name: string;
  thumbnailUrl: string | null;
  productType: CategoryProperties_category_products_edges_node_productType;
}

export interface CategoryProperties_category_products_edges {
  __typename: "ProductCountableEdge";
  cursor: string;
  node: CategoryProperties_category_products_edges_node;
}

export interface CategoryProperties_category_products {
  __typename: "ProductCountableConnection";
  pageInfo: CategoryProperties_category_products_pageInfo;
  edges: CategoryProperties_category_products_edges[];
}

export interface CategoryProperties_category {
  __typename: "Category";
  id: string;
  name: string;
  description: string;
  parent: CategoryProperties_category_parent | null;
  children: CategoryProperties_category_children | null;
  products: CategoryProperties_category_products | null;
}

export interface CategoryProperties {
  category: CategoryProperties_category | null;
}

export interface CategoryPropertiesVariables {
  id: string;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
