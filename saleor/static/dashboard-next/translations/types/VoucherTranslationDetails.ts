/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: VoucherTranslationDetails
// ====================================================

export interface VoucherTranslationDetails_voucher_translation_language {
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

export interface VoucherTranslationDetails_voucher_translation {
  __typename: "VoucherTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Translation's language
   */
  language: VoucherTranslationDetails_voucher_translation_language;
  name: string | null;
}

export interface VoucherTranslationDetails_voucher {
  __typename: "Voucher";
  /**
   * The ID of the object.
   */
  id: string;
  name: string | null;
  /**
   * Returns translated Voucher fields for the given language code.
   */
  translation: VoucherTranslationDetails_voucher_translation | null;
}

export interface VoucherTranslationDetails {
  /**
   * Lookup a voucher by ID.
   */
  voucher: VoucherTranslationDetails_voucher | null;
}

export interface VoucherTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
