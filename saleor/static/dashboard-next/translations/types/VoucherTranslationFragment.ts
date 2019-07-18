/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: VoucherTranslationFragment
// ====================================================

export interface VoucherTranslationFragment_translation_language {
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

export interface VoucherTranslationFragment_translation {
  __typename: "VoucherTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Translation's language
   */
  language: VoucherTranslationFragment_translation_language;
  name: string | null;
}

export interface VoucherTranslationFragment {
  __typename: "Voucher";
  /**
   * The ID of the object.
   */
  id: string;
  name: string | null;
  /**
   * Returns translated Voucher fields for the given language code.
   */
  translation: VoucherTranslationFragment_translation | null;
}
