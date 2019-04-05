/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: PageTranslations
// ====================================================

export interface PageTranslations_pages_edges_node_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface PageTranslations_pages_edges_node_translation {
  __typename: "PageTranslation";
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  language: PageTranslations_pages_edges_node_translation_language;
}

export interface PageTranslations_pages_edges_node {
  __typename: "Page";
  id: string;
  contentJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  title: string;
  translation: PageTranslations_pages_edges_node_translation | null;
}

export interface PageTranslations_pages_edges {
  __typename: "PageCountableEdge";
  node: PageTranslations_pages_edges_node;
}

export interface PageTranslations_pages_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface PageTranslations_pages {
  __typename: "PageCountableConnection";
  edges: PageTranslations_pages_edges[];
  pageInfo: PageTranslations_pages_pageInfo;
}

export interface PageTranslations {
  pages: PageTranslations_pages | null;
}

export interface PageTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
