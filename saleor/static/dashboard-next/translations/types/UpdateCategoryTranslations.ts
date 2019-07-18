/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { TranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateCategoryTranslations
// ====================================================

export interface UpdateCategoryTranslations_categoryTranslate_errors {
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

export interface UpdateCategoryTranslations_categoryTranslate_category_translation_language {
  __typename: "LanguageDisplay";
  /**
   * Language.
   */
  language: string;
}

export interface UpdateCategoryTranslations_categoryTranslate_category_translation {
  __typename: "CategoryTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  descriptionJson: any;
  /**
   * Translation's language
   */
  language: UpdateCategoryTranslations_categoryTranslate_category_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface UpdateCategoryTranslations_categoryTranslate_category {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  /**
   * Returns translated Category fields for the given language code.
   */
  translation: UpdateCategoryTranslations_categoryTranslate_category_translation | null;
}

export interface UpdateCategoryTranslations_categoryTranslate {
  __typename: "CategoryTranslate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: UpdateCategoryTranslations_categoryTranslate_errors[] | null;
  category: UpdateCategoryTranslations_categoryTranslate_category | null;
}

export interface UpdateCategoryTranslations {
  /**
   * Creates/Updates translations for Category.
   */
  categoryTranslate: UpdateCategoryTranslations_categoryTranslate | null;
}

export interface UpdateCategoryTranslationsVariables {
  id: string;
  input: TranslationInput;
  language: LanguageCodeEnum;
}
