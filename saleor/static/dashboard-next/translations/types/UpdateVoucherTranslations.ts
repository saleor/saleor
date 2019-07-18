/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { NameTranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateVoucherTranslations
// ====================================================

export interface UpdateVoucherTranslations_voucherTranslate_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface UpdateVoucherTranslations_voucherTranslate_voucher_translation_language {
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

export interface UpdateVoucherTranslations_voucherTranslate_voucher_translation {
  __typename: "VoucherTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Translation's language
   */
  language: UpdateVoucherTranslations_voucherTranslate_voucher_translation_language;
  name: string | null;
}

export interface UpdateVoucherTranslations_voucherTranslate_voucher {
  __typename: "Voucher";
  /**
   * The ID of the object.
   */
  id: string;
  name: string | null;
  /**
   * Returns translated Voucher fields for the given language code.
   */
  translation: UpdateVoucherTranslations_voucherTranslate_voucher_translation | null;
}

export interface UpdateVoucherTranslations_voucherTranslate {
  __typename: "VoucherTranslate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: UpdateVoucherTranslations_voucherTranslate_errors[] | null;
  voucher: UpdateVoucherTranslations_voucherTranslate_voucher | null;
}

export interface UpdateVoucherTranslations {
  /**
   * Creates/Updates translations for Voucher.
   */
  voucherTranslate: UpdateVoucherTranslations_voucherTranslate | null;
}

export interface UpdateVoucherTranslationsVariables {
  id: string;
  input: NameTranslationInput;
  language: LanguageCodeEnum;
}
