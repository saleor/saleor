/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SaleTranslations
// ====================================================

export interface SaleTranslations_sales_edges_node_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface SaleTranslations_sales_edges_node_translation {
  __typename: "SaleTranslation";
  id: string;
  language: SaleTranslations_sales_edges_node_translation_language;
  name: string | null;
}

export interface SaleTranslations_sales_edges_node {
  __typename: "Sale";
  id: string;
  name: string;
  translation: SaleTranslations_sales_edges_node_translation | null;
}

export interface SaleTranslations_sales_edges {
  __typename: "SaleCountableEdge";
  node: SaleTranslations_sales_edges_node;
}

export interface SaleTranslations_sales_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface SaleTranslations_sales {
  __typename: "SaleCountableConnection";
  edges: SaleTranslations_sales_edges[];
  pageInfo: SaleTranslations_sales_pageInfo;
}

export interface SaleTranslations {
  sales: SaleTranslations_sales | null;
}

export interface SaleTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
