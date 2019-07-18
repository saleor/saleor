/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CategoryTranslationDetails
// ====================================================

export interface CategoryTranslationDetails_category_translation_language {
  __typename: "LanguageDisplay";
  /**
   * Language.
   */
  language: string;
}

export interface CategoryTranslationDetails_category_translation {
  __typename: "CategoryTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  descriptionJson: any;
  /**
   * Translation's language
   */
  language: CategoryTranslationDetails_category_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CategoryTranslationDetails_category {
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
  translation: CategoryTranslationDetails_category_translation | null;
}

export interface CategoryTranslationDetails {
  /**
   * Lookup a category by ID.
   */
  category: CategoryTranslationDetails_category | null;
}

export interface CategoryTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
