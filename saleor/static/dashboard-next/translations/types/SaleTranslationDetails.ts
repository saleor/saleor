/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SaleTranslationDetails
// ====================================================

export interface SaleTranslationDetails_sale_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface SaleTranslationDetails_sale_translation {
  __typename: "SaleTranslation";
  id: string;
  language: SaleTranslationDetails_sale_translation_language;
  name: string | null;
}

export interface SaleTranslationDetails_sale {
  __typename: "Sale";
  id: string;
  name: string;
  translation: SaleTranslationDetails_sale_translation | null;
}

export interface SaleTranslationDetails {
  sale: SaleTranslationDetails_sale | null;
}

export interface SaleTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
