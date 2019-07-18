/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CollectionTranslationFragment
// ====================================================

export interface CollectionTranslationFragment_translation_language {
  __typename: "LanguageDisplay";
  /**
   * Language.
   */
  language: string;
}

export interface CollectionTranslationFragment_translation {
  __typename: "CollectionTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  descriptionJson: any;
  /**
   * Translation's language
   */
  language: CollectionTranslationFragment_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CollectionTranslationFragment {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  /**
   * Returns translated Collection fields for the given language code.
   */
  translation: CollectionTranslationFragment_translation | null;
}
