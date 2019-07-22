/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTranslations
// ====================================================

export interface ProductTranslations_products_edges_node_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface ProductTranslations_products_edges_node_translation {
  __typename: "ProductTranslation";
  id: string;
  descriptionJson: any;
  language: ProductTranslations_products_edges_node_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface ProductTranslations_products_edges_node {
  __typename: "Product";
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  translation: ProductTranslations_products_edges_node_translation | null;
}

export interface ProductTranslations_products_edges {
  __typename: "ProductCountableEdge";
  node: ProductTranslations_products_edges_node;
}

export interface ProductTranslations_products_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface ProductTranslations_products {
  __typename: "ProductCountableConnection";
  edges: ProductTranslations_products_edges[];
  pageInfo: ProductTranslations_products_pageInfo;
}

export interface ProductTranslations {
  products: ProductTranslations_products | null;
}

export interface ProductTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
