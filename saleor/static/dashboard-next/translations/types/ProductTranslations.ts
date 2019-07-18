/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTranslations
// ====================================================

export interface ProductTranslations_products_edges_node_translation_language {
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

export interface ProductTranslations_products_edges_node_translation {
  __typename: "ProductTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  descriptionJson: any;
  /**
   * Translation's language
   */
  language: ProductTranslations_products_edges_node_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface ProductTranslations_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  /**
   * Returns translated Product fields for the given language code.
   */
  translation: ProductTranslations_products_edges_node_translation | null;
}

export interface ProductTranslations_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: ProductTranslations_products_edges_node;
}

export interface ProductTranslations_products_pageInfo {
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

export interface ProductTranslations_products {
  __typename: "ProductCountableConnection";
  edges: ProductTranslations_products_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: ProductTranslations_products_pageInfo;
}

export interface ProductTranslations {
  /**
   * List of the shop's products.
   */
  products: ProductTranslations_products | null;
}

export interface ProductTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
