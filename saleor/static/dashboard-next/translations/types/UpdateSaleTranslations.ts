/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { NameTranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateSaleTranslations
// ====================================================

export interface UpdateSaleTranslations_saleTranslate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UpdateSaleTranslations_saleTranslate_sale_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface UpdateSaleTranslations_saleTranslate_sale_translation {
  __typename: "SaleTranslation";
  id: string;
  language: UpdateSaleTranslations_saleTranslate_sale_translation_language;
  name: string | null;
}

export interface UpdateSaleTranslations_saleTranslate_sale {
  __typename: "Sale";
  id: string;
  name: string;
  translation: UpdateSaleTranslations_saleTranslate_sale_translation | null;
}

export interface UpdateSaleTranslations_saleTranslate {
  __typename: "SaleTranslate";
  errors: UpdateSaleTranslations_saleTranslate_errors[] | null;
  sale: UpdateSaleTranslations_saleTranslate_sale | null;
}

export interface UpdateSaleTranslations {
  saleTranslate: UpdateSaleTranslations_saleTranslate | null;
}

export interface UpdateSaleTranslationsVariables {
  id: string;
  input: NameTranslationInput;
  language: LanguageCodeEnum;
}
