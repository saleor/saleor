/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CollectionTranslations
// ====================================================

export interface CollectionTranslations_collections_edges_node_translation_language {
  __typename: "LanguageDisplay";
  /**
   * Language.
   */
  language: string;
}

export interface CollectionTranslations_collections_edges_node_translation {
  __typename: "CollectionTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  descriptionJson: any;
  /**
   * Translation's language
   */
  language: CollectionTranslations_collections_edges_node_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CollectionTranslations_collections_edges_node {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  /**
   * Returns translated Collection fields for the given language code.
   */
  translation: CollectionTranslations_collections_edges_node_translation | null;
}

export interface CollectionTranslations_collections_edges {
  __typename: "CollectionCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: CollectionTranslations_collections_edges_node;
}

export interface CollectionTranslations_collections_pageInfo {
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

export interface CollectionTranslations_collections {
  __typename: "CollectionCountableConnection";
  edges: CollectionTranslations_collections_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: CollectionTranslations_collections_pageInfo;
}

export interface CollectionTranslations {
  /**
   * List of the shop's collections.
   */
  collections: CollectionTranslations_collections | null;
}

export interface CollectionTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
