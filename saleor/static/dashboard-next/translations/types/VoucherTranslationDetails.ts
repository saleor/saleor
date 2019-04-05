/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: VoucherTranslationDetails
// ====================================================

export interface VoucherTranslationDetails_voucher_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface VoucherTranslationDetails_voucher_translation {
  __typename: "VoucherTranslation";
  id: string;
  language: VoucherTranslationDetails_voucher_translation_language;
  name: string | null;
}

export interface VoucherTranslationDetails_voucher {
  __typename: "Voucher";
  id: string;
  name: string | null;
  translation: VoucherTranslationDetails_voucher_translation | null;
}

export interface VoucherTranslationDetails {
  voucher: VoucherTranslationDetails_voucher | null;
}

export interface VoucherTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
