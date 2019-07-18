/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTypeTranslations
// ====================================================

export interface ProductTypeTranslations_productTypes_edges_node_productAttributes_translation {
  __typename: "AttributeTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslations_productTypes_edges_node_productAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslations_productTypes_edges_node_productAttributes_values {
  __typename: "AttributeValue";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of a value displayed in the interface.
   */
  name: string | null;
  /**
   * Returns translated Attribute Value fields for the given language code.
   */
  translation: ProductTypeTranslations_productTypes_edges_node_productAttributes_values_translation | null;
}

export interface ProductTypeTranslations_productTypes_edges_node_productAttributes {
  __typename: "Attribute";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of an attribute displayed in the interface.
   */
  name: string | null;
  /**
   * Returns translated Attribute fields for the given language code.
   */
  translation: ProductTypeTranslations_productTypes_edges_node_productAttributes_translation | null;
  /**
   * List of attribute's values.
   */
  values: (ProductTypeTranslations_productTypes_edges_node_productAttributes_values | null)[] | null;
}

export interface ProductTypeTranslations_productTypes_edges_node_variantAttributes_translation {
  __typename: "AttributeTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslations_productTypes_edges_node_variantAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslations_productTypes_edges_node_variantAttributes_values {
  __typename: "AttributeValue";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of a value displayed in the interface.
   */
  name: string | null;
  /**
   * Returns translated Attribute Value fields for the given language code.
   */
  translation: ProductTypeTranslations_productTypes_edges_node_variantAttributes_values_translation | null;
}

export interface ProductTypeTranslations_productTypes_edges_node_variantAttributes {
  __typename: "Attribute";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Name of an attribute displayed in the interface.
   */
  name: string | null;
  /**
   * Returns translated Attribute fields for the given language code.
   */
  translation: ProductTypeTranslations_productTypes_edges_node_variantAttributes_translation | null;
  /**
   * List of attribute's values.
   */
  values: (ProductTypeTranslations_productTypes_edges_node_variantAttributes_values | null)[] | null;
}

export interface ProductTypeTranslations_productTypes_edges_node {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * Product attributes of that product type.
   */
  productAttributes: (ProductTypeTranslations_productTypes_edges_node_productAttributes | null)[] | null;
  /**
   * Variant attributes of that product type.
   */
  variantAttributes: (ProductTypeTranslations_productTypes_edges_node_variantAttributes | null)[] | null;
}

export interface ProductTypeTranslations_productTypes_edges {
  __typename: "ProductTypeCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: ProductTypeTranslations_productTypes_edges_node;
}

export interface ProductTypeTranslations_productTypes_pageInfo {
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

export interface ProductTypeTranslations_productTypes {
  __typename: "ProductTypeCountableConnection";
  edges: ProductTypeTranslations_productTypes_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: ProductTypeTranslations_productTypes_pageInfo;
}

export interface ProductTypeTranslations {
  /**
   * List of the shop's product types.
   */
  productTypes: ProductTypeTranslations_productTypes | null;
}

export interface ProductTypeTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
