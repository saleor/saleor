/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: ShippingMethodTranslationFragment
// ====================================================

export interface ShippingMethodTranslationFragment_translation_language {
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

export interface ShippingMethodTranslationFragment_translation {
  __typename: "ShippingMethodTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Translation's language
   */
  language: ShippingMethodTranslationFragment_translation_language;
  name: string | null;
}

export interface ShippingMethodTranslationFragment {
  __typename: "ShippingMethod";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * Returns translated Shipping Method fields for the given language code.
   */
  translation: ShippingMethodTranslationFragment_translation | null;
}
