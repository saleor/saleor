/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: VoucherTranslationFragment
// ====================================================

export interface VoucherTranslationFragment_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface VoucherTranslationFragment_translation {
  __typename: "VoucherTranslation";
  id: string;
  language: VoucherTranslationFragment_translation_language;
  name: string | null;
}

export interface VoucherTranslationFragment {
  __typename: "Voucher";
  id: string;
  name: string | null;
  translation: VoucherTranslationFragment_translation | null;
}
