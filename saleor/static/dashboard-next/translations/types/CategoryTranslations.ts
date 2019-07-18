/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CategoryTranslations
// ====================================================

export interface CategoryTranslations_categories_edges_node_translation_language {
  __typename: "LanguageDisplay";
  /**
   * Language.
   */
  language: string;
}

export interface CategoryTranslations_categories_edges_node_translation {
  __typename: "CategoryTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  descriptionJson: any;
  /**
   * Translation's language
   */
  language: CategoryTranslations_categories_edges_node_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CategoryTranslations_categories_edges_node {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  /**
   * Returns translated Category fields for the given language code.
   */
  translation: CategoryTranslations_categories_edges_node_translation | null;
}

export interface CategoryTranslations_categories_edges {
  __typename: "CategoryCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: CategoryTranslations_categories_edges_node;
}

export interface CategoryTranslations_categories_pageInfo {
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

export interface CategoryTranslations_categories {
  __typename: "CategoryCountableConnection";
  edges: CategoryTranslations_categories_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: CategoryTranslations_categories_pageInfo;
}

export interface CategoryTranslations {
  /**
   * List of the shop's categories.
   */
  categories: CategoryTranslations_categories | null;
}

export interface CategoryTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
