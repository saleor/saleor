/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { NameTranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateSaleTranslations
// ====================================================

export interface UpdateSaleTranslations_saleTranslate_errors {
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

export interface UpdateSaleTranslations_saleTranslate_sale_translation_language {
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

export interface UpdateSaleTranslations_saleTranslate_sale_translation {
  __typename: "SaleTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Translation's language
   */
  language: UpdateSaleTranslations_saleTranslate_sale_translation_language;
  name: string | null;
}

export interface UpdateSaleTranslations_saleTranslate_sale {
  __typename: "Sale";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * Returns translated sale fields for the given language code.
   */
  translation: UpdateSaleTranslations_saleTranslate_sale_translation | null;
}

export interface UpdateSaleTranslations_saleTranslate {
  __typename: "SaleTranslate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: UpdateSaleTranslations_saleTranslate_errors[] | null;
  sale: UpdateSaleTranslations_saleTranslate_sale | null;
}

export interface UpdateSaleTranslations {
  /**
   * Creates/updates translations for a sale.
   */
  saleTranslate: UpdateSaleTranslations_saleTranslate | null;
}

export interface UpdateSaleTranslationsVariables {
  id: string;
  input: NameTranslationInput;
  language: LanguageCodeEnum;
}
