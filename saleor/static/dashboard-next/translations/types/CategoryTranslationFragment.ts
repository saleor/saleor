/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CategoryTranslationFragment
// ====================================================

export interface CategoryTranslationFragment_translation_language {
  __typename: "LanguageDisplay";
  language: string;
}

export interface CategoryTranslationFragment_translation {
  __typename: "CategoryTranslation";
  id: string;
  descriptionJson: any;
  language: CategoryTranslationFragment_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CategoryTranslationFragment {
  __typename: "Category";
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  translation: CategoryTranslationFragment_translation | null;
}
