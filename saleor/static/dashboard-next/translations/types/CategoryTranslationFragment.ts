/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CategoryTranslationFragment
// ====================================================

export interface CategoryTranslationFragment_translation_language {
  __typename: "LanguageDisplay";
  /**
   * Language.
   */
  language: string;
}

export interface CategoryTranslationFragment_translation {
  __typename: "CategoryTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  descriptionJson: any;
  /**
   * Translation's language
   */
  language: CategoryTranslationFragment_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CategoryTranslationFragment {
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
  translation: CategoryTranslationFragment_translation | null;
}
