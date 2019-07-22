/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CollectionTranslations
// ====================================================

export interface CollectionTranslations_collections_edges_node_translation_language {
  __typename: "LanguageDisplay";
  language: string;
}

export interface CollectionTranslations_collections_edges_node_translation {
  __typename: "CollectionTranslation";
  id: string;
  descriptionJson: any;
  language: CollectionTranslations_collections_edges_node_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CollectionTranslations_collections_edges_node {
  __typename: "Collection";
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  translation: CollectionTranslations_collections_edges_node_translation | null;
}

export interface CollectionTranslations_collections_edges {
  __typename: "CollectionCountableEdge";
  node: CollectionTranslations_collections_edges_node;
}

export interface CollectionTranslations_collections_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface CollectionTranslations_collections {
  __typename: "CollectionCountableConnection";
  edges: CollectionTranslations_collections_edges[];
  pageInfo: CollectionTranslations_collections_pageInfo;
}

export interface CollectionTranslations {
  collections: CollectionTranslations_collections | null;
}

export interface CollectionTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
