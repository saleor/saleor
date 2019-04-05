/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CategoryTranslations
// ====================================================

export interface CategoryTranslations_categories_edges_node_translation_language {
  __typename: "LanguageDisplay";
  language: string;
}

export interface CategoryTranslations_categories_edges_node_translation {
  __typename: "CategoryTranslation";
  id: string;
  descriptionJson: any;
  language: CategoryTranslations_categories_edges_node_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CategoryTranslations_categories_edges_node {
  __typename: "Category";
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  translation: CategoryTranslations_categories_edges_node_translation | null;
}

export interface CategoryTranslations_categories_edges {
  __typename: "CategoryCountableEdge";
  node: CategoryTranslations_categories_edges_node;
}

export interface CategoryTranslations_categories_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface CategoryTranslations_categories {
  __typename: "CategoryCountableConnection";
  edges: CategoryTranslations_categories_edges[];
  pageInfo: CategoryTranslations_categories_pageInfo;
}

export interface CategoryTranslations {
  categories: CategoryTranslations_categories | null;
}

export interface CategoryTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
