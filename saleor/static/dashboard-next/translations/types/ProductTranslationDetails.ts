/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: ProductTranslationDetails
// ====================================================

export interface ProductTranslationDetails_product_translation_language {
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

export interface ProductTranslationDetails_product_translation {
  __typename: "ProductTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  descriptionJson: any;
  /**
   * Translation's language
   */
  language: ProductTranslationDetails_product_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface ProductTranslationDetails_product {
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
  translation: ProductTranslationDetails_product_translation | null;
}

export interface ProductTranslationDetails {
  /**
   * Lookup a product by ID.
   */
  product: ProductTranslationDetails_product | null;
}

export interface ProductTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
