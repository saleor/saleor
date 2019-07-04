/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTypeTranslationDetails
// ====================================================

export interface ProductTypeTranslationDetails_productType_productAttributes_translation {
  __typename: "AttributeTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslationDetails_productType_productAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslationDetails_productType_productAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  translation: ProductTypeTranslationDetails_productType_productAttributes_values_translation | null;
}

export interface ProductTypeTranslationDetails_productType_productAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  translation: ProductTypeTranslationDetails_productType_productAttributes_translation | null;
  values: (ProductTypeTranslationDetails_productType_productAttributes_values | null)[] | null;
}

export interface ProductTypeTranslationDetails_productType_variantAttributes_translation {
  __typename: "AttributeTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslationDetails_productType_variantAttributes_values_translation {
  __typename: "AttributeValueTranslation";
  id: string;
  name: string;
}

export interface ProductTypeTranslationDetails_productType_variantAttributes_values {
  __typename: "AttributeValue";
  id: string;
  name: string | null;
  translation: ProductTypeTranslationDetails_productType_variantAttributes_values_translation | null;
}

export interface ProductTypeTranslationDetails_productType_variantAttributes {
  __typename: "Attribute";
  id: string;
  name: string | null;
  translation: ProductTypeTranslationDetails_productType_variantAttributes_translation | null;
  values: (ProductTypeTranslationDetails_productType_variantAttributes_values | null)[] | null;
}

export interface ProductTypeTranslationDetails_productType {
  __typename: "ProductType";
  id: string;
  name: string;
  productAttributes: (ProductTypeTranslationDetails_productType_productAttributes | null)[] | null;
  variantAttributes: (ProductTypeTranslationDetails_productType_variantAttributes | null)[] | null;
}

export interface ProductTypeTranslationDetails {
  productType: ProductTypeTranslationDetails_productType | null;
}

export interface ProductTypeTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
