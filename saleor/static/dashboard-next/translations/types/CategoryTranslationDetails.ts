/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CategoryTranslationDetails
// ====================================================

export interface CategoryTranslationDetails_category_translation_language {
  __typename: "LanguageDisplay";
  language: string;
}

export interface CategoryTranslationDetails_category_translation {
  __typename: "CategoryTranslation";
  id: string;
  descriptionJson: any;
  language: CategoryTranslationDetails_category_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CategoryTranslationDetails_category {
  __typename: "Category";
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  translation: CategoryTranslationDetails_category_translation | null;
}

export interface CategoryTranslationDetails {
  category: CategoryTranslationDetails_category | null;
}

export interface CategoryTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
