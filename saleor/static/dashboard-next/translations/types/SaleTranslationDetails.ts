/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SaleTranslationDetails
// ====================================================

export interface SaleTranslationDetails_sale_translation_language {
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

export interface SaleTranslationDetails_sale_translation {
  __typename: "SaleTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Translation's language
   */
  language: SaleTranslationDetails_sale_translation_language;
  name: string | null;
}

export interface SaleTranslationDetails_sale {
  __typename: "Sale";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * Returns translated sale fields for the given language code.
   */
  translation: SaleTranslationDetails_sale_translation | null;
}

export interface SaleTranslationDetails {
  /**
   * Lookup a sale by ID.
   */
  sale: SaleTranslationDetails_sale | null;
}

export interface SaleTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
