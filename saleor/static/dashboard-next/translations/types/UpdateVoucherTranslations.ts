/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { NameTranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateVoucherTranslations
// ====================================================

export interface UpdateVoucherTranslations_voucherTranslate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UpdateVoucherTranslations_voucherTranslate_voucher_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface UpdateVoucherTranslations_voucherTranslate_voucher_translation {
  __typename: "VoucherTranslation";
  id: string;
  language: UpdateVoucherTranslations_voucherTranslate_voucher_translation_language;
  name: string | null;
}

export interface UpdateVoucherTranslations_voucherTranslate_voucher {
  __typename: "Voucher";
  id: string;
  name: string | null;
  translation: UpdateVoucherTranslations_voucherTranslate_voucher_translation | null;
}

export interface UpdateVoucherTranslations_voucherTranslate {
  __typename: "VoucherTranslate";
  errors: UpdateVoucherTranslations_voucherTranslate_errors[] | null;
  voucher: UpdateVoucherTranslations_voucherTranslate_voucher | null;
}

export interface UpdateVoucherTranslations {
  voucherTranslate: UpdateVoucherTranslations_voucherTranslate | null;
}

export interface UpdateVoucherTranslationsVariables {
  id: string;
  input: NameTranslationInput;
  language: LanguageCodeEnum;
}
