/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PageTranslations
// ====================================================

export interface PageTranslations_pages_edges_node_translation_language {
  __typename: "LanguageDisplay";
  /**
   * Language code.
   */
  code: LanguageCodeEnum;
  /**
   * Language.
   */
  language: string;
}

export interface PageTranslations_pages_edges_node_translation {
  __typename: "PageTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  /**
   * Translation's language
   */
  language: PageTranslations_pages_edges_node_translation_language;
}

export interface PageTranslations_pages_edges_node {
  __typename: "Page";
  /**
   * The ID of the object.
   */
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  /**
   * Returns translated Page fields for the given language code.
   */
  translation: PageTranslations_pages_edges_node_translation | null;
}

export interface PageTranslations_pages_edges {
  __typename: "PageCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: PageTranslations_pages_edges_node;
}

export interface PageTranslations_pages_pageInfo {
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

export interface PageTranslations_pages {
  __typename: "PageCountableConnection";
  edges: PageTranslations_pages_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: PageTranslations_pages_pageInfo;
}

export interface PageTranslations {
  /**
   * List of the shop's pages.
   */
  pages: PageTranslations_pages | null;
}

export interface PageTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
