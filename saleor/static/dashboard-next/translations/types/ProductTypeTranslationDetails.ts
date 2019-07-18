/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTypeTranslationDetails
// ====================================================

export interface ProductTypeTranslationDetails_productType_productAttributes_translation {
  __typename: "AttributeTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslationDetails_productType_productAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslationDetails_productType_productAttributes_values {
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
  translation: ProductTypeTranslationDetails_productType_productAttributes_values_translation | null;
}

export interface ProductTypeTranslationDetails_productType_productAttributes {
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
  translation: ProductTypeTranslationDetails_productType_productAttributes_translation | null;
  /**
   * List of attribute's values.
   */
  values: (ProductTypeTranslationDetails_productType_productAttributes_values | null)[] | null;
}

export interface ProductTypeTranslationDetails_productType_variantAttributes_translation {
  __typename: "AttributeTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslationDetails_productType_variantAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface ProductTypeTranslationDetails_productType_variantAttributes_values {
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
  translation: ProductTypeTranslationDetails_productType_variantAttributes_values_translation | null;
}

export interface ProductTypeTranslationDetails_productType_variantAttributes {
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
  translation: ProductTypeTranslationDetails_productType_variantAttributes_translation | null;
  /**
   * List of attribute's values.
   */
  values: (ProductTypeTranslationDetails_productType_variantAttributes_values | null)[] | null;
}

export interface ProductTypeTranslationDetails_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * Product attributes of that product type.
   */
  productAttributes: (ProductTypeTranslationDetails_productType_productAttributes | null)[] | null;
  /**
   * Variant attributes of that product type.
   */
  variantAttributes: (ProductTypeTranslationDetails_productType_variantAttributes | null)[] | null;
}

export interface ProductTypeTranslationDetails {
  /**
   * Lookup a product type by ID.
   */
  productType: ProductTypeTranslationDetails_productType | null;
}

export interface ProductTypeTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
