/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTypeTranslations
// ====================================================

export interface ProductTypeTranslations_productTypes_edges_node_productAttributes_translation {
  __typename: "AttributeTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslations_productTypes_edges_node_productAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslations_productTypes_edges_node_productAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  translation: ProductTypeTranslations_productTypes_edges_node_productAttributes_values_translation | null;
}

export interface ProductTypeTranslations_productTypes_edges_node_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  translation: ProductTypeTranslations_productTypes_edges_node_productAttributes_translation | null;
  values: (ProductTypeTranslations_productTypes_edges_node_productAttributes_values | null)[] | null;
}

export interface ProductTypeTranslations_productTypes_edges_node_variantAttributes_translation {
  __typename: "AttributeTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslations_productTypes_edges_node_variantAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslations_productTypes_edges_node_variantAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  translation: ProductTypeTranslations_productTypes_edges_node_variantAttributes_values_translation | null;
}

export interface ProductTypeTranslations_productTypes_edges_node_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  translation: ProductTypeTranslations_productTypes_edges_node_variantAttributes_translation | null;
  values: (ProductTypeTranslations_productTypes_edges_node_variantAttributes_values | null)[] | null;
}

export interface ProductTypeTranslations_productTypes_edges_node {
  __typename: "ProductType";
  id: string;
  name: string;
  productAttributes: (ProductTypeTranslations_productTypes_edges_node_productAttributes | null)[] | null;
  variantAttributes: (ProductTypeTranslations_productTypes_edges_node_variantAttributes | null)[] | null;
}

export interface ProductTypeTranslations_productTypes_edges {
  __typename: "ProductTypeCountableEdge";
  node: ProductTypeTranslations_productTypes_edges_node;
}

export interface ProductTypeTranslations_productTypes_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface ProductTypeTranslations_productTypes {
  __typename: "ProductTypeCountableConnection";
  edges: ProductTypeTranslations_productTypes_edges[];
  pageInfo: ProductTypeTranslations_productTypes_pageInfo;
}

export interface ProductTypeTranslations {
  productTypes: ProductTypeTranslations_productTypes | null;
}

export interface ProductTypeTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
