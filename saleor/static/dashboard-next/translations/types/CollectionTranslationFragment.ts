/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL fragment: CollectionTranslationFragment
// ====================================================

export interface CollectionTranslationFragment_translation_language {
  __typename: "LanguageDisplay";
  language: string;
}

export interface CollectionTranslationFragment_translation {
  __typename: "CollectionTranslation";
  id: string;
  descriptionJson: any;
  language: CollectionTranslationFragment_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CollectionTranslationFragment {
  __typename: "Collection";
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  translation: CollectionTranslationFragment_translation | null;
}
