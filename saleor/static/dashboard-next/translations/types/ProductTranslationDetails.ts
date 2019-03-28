/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTranslationDetails
// ====================================================

export interface ProductTranslationDetails_product_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface ProductTranslationDetails_product_translation {
  __typename: "ProductTranslation";
  id: string;
  descriptionJson: any;
  language: ProductTranslationDetails_product_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface ProductTranslationDetails_product {
  __typename: "Product";
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  translation: ProductTranslationDetails_product_translation | null;
}

export interface ProductTranslationDetails {
  product: ProductTranslationDetails_product | null;
}

export interface ProductTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
