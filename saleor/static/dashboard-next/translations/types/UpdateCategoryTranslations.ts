/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { TranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateCategoryTranslations
// ====================================================

export interface UpdateCategoryTranslations_categoryTranslate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UpdateCategoryTranslations_categoryTranslate_category_translation_language {
  __typename: "LanguageDisplay";
  language: string;
}

export interface UpdateCategoryTranslations_categoryTranslate_category_translation {
  __typename: "CategoryTranslation";
  id: string;
  descriptionJson: any;
  language: UpdateCategoryTranslations_categoryTranslate_category_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface UpdateCategoryTranslations_categoryTranslate_category {
  __typename: "Category";
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  translation: UpdateCategoryTranslations_categoryTranslate_category_translation | null;
}

export interface UpdateCategoryTranslations_categoryTranslate {
  __typename: "CategoryTranslate";
  errors: UpdateCategoryTranslations_categoryTranslate_errors[] | null;
  category: UpdateCategoryTranslations_categoryTranslate_category | null;
}

export interface UpdateCategoryTranslations {
  categoryTranslate: UpdateCategoryTranslations_categoryTranslate | null;
}

export interface UpdateCategoryTranslationsVariables {
  id: string;
  input: TranslationInput;
  language: LanguageCodeEnum;
}
