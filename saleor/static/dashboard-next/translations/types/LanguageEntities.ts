/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum, TranslatableKinds } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: LanguageEntities
// ====================================================

export interface LanguageEntities_translations_edges_node_Collection {
  __typename: "Collection" | "Attribute" | "AttributeValue" | "ProductVariant" | "Page" | "ShippingMethod" | "Voucher" | "MenuItem";
}

export interface LanguageEntities_translations_edges_node_Product_translation_language {
  __typename: "LanguageDisplay";
  language: string;
}

export interface LanguageEntities_translations_edges_node_Product_translation {
  __typename: "ProductTranslation";
  id: string;
  description: string;
  descriptionJson: any;
  language: LanguageEntities_translations_edges_node_Product_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface LanguageEntities_translations_edges_node_Product {
  __typename: "Product";
  id: string;
  name: string;
  translation: LanguageEntities_translations_edges_node_Product_translation | null;
}

export interface LanguageEntities_translations_edges_node_Category_translation_language {
  __typename: "LanguageDisplay";
  language: string;
}

export interface LanguageEntities_translations_edges_node_Category_translation {
  __typename: "CategoryTranslation";
  id: string;
  description: string;
  descriptionJson: any;
  language: LanguageEntities_translations_edges_node_Category_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface LanguageEntities_translations_edges_node_Category {
  __typename: "Category";
  id: string;
  name: string;
  translation: LanguageEntities_translations_edges_node_Category_translation | null;
}

export type LanguageEntities_translations_edges_node = LanguageEntities_translations_edges_node_Collection | LanguageEntities_translations_edges_node_Product | LanguageEntities_translations_edges_node_Category;

export interface LanguageEntities_translations_edges {
  __typename: "TranslatableItemEdge";
  node: LanguageEntities_translations_edges_node;
}

export interface LanguageEntities_translations_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface LanguageEntities_translations {
  __typename: "TranslatableItemConnection";
  edges: LanguageEntities_translations_edges[];
  pageInfo: LanguageEntities_translations_pageInfo;
}

export interface LanguageEntities {
  translations: LanguageEntities_translations | null;
}

export interface LanguageEntitiesVariables {
  language: LanguageCodeEnum;
  kind: TranslatableKinds;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
