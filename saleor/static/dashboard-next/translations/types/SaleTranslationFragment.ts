/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: SaleTranslationFragment
// ====================================================

export interface SaleTranslationFragment_translation_language {
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

export interface SaleTranslationFragment_translation {
  __typename: "SaleTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Translation's language
   */
  language: SaleTranslationFragment_translation_language;
  name: string | null;
}

export interface SaleTranslationFragment {
  __typename: "Sale";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * Returns translated sale fields for the given language code.
   */
  translation: SaleTranslationFragment_translation | null;
}
