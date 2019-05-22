/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL query operation: CategoryDetails
// ====================================================

export interface CategoryDetails_category_backgroundImage {
  __typename: "Image";
  alt: string | null;
  url: string;
}

export interface CategoryDetails_category_parent {
  __typename: "Category";
  id: string;
}

export interface CategoryDetails_category_children_edges_node_children {
  __typename: "CategoryCountableConnection";
  totalCount: number | null;
}

export interface CategoryDetails_category_children_edges_node_products {
  __typename: "ProductCountableConnection";
  totalCount: number | null;
}

export interface CategoryDetails_category_children_edges_node {
  __typename: "Category";
  id: string;
  name: string;
  children: CategoryDetails_category_children_edges_node_children | null;
  products: CategoryDetails_category_children_edges_node_products | null;
}

export interface CategoryDetails_category_children_edges {
  __typename: "CategoryCountableEdge";
  node: CategoryDetails_category_children_edges_node;
}

export interface CategoryDetails_category_children {
  __typename: "CategoryCountableConnection";
  edges: CategoryDetails_category_children_edges[];
}

export interface CategoryDetails_category_products_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface CategoryDetails_category_products_edges_node_basePrice {
  __typename: "Money";
  amount: number;
  currency: string;
}

export interface CategoryDetails_category_products_edges_node_thumbnail {
  __typename: "Image";
  url: string;
}

export interface CategoryDetails_category_products_edges_node_productType {
  __typename: "ProductType";
  id: string;
  name: string;
}

export interface CategoryDetails_category_products_edges_node {
  __typename: "Product";
  id: string;
  name: string;
  basePrice: CategoryDetails_category_products_edges_node_basePrice | null;
  isAvailable: boolean | null;
  thumbnail: CategoryDetails_category_products_edges_node_thumbnail | null;
  productType: CategoryDetails_category_products_edges_node_productType;
}

export interface CategoryDetails_category_products_edges {
  __typename: "ProductCountableEdge";
  cursor: string;
  node: CategoryDetails_category_products_edges_node;
}

export interface CategoryDetails_category_products {
  __typename: "ProductCountableConnection";
  pageInfo: CategoryDetails_category_products_pageInfo;
  edges: CategoryDetails_category_products_edges[];
}

export interface CategoryDetails_category {
  __typename: "Category";
  id: string;
  backgroundImage: CategoryDetails_category_backgroundImage | null;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  parent: CategoryDetails_category_parent | null;
  children: CategoryDetails_category_children | null;
  products: CategoryDetails_category_products | null;
}

export interface CategoryDetails {
  category: CategoryDetails_category | null;
}

export interface CategoryDetailsVariables {
  id: string;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
