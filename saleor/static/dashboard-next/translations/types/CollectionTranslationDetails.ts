/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CollectionTranslationDetails
// ====================================================

export interface CollectionTranslationDetails_collection_translation_language {
  __typename: "LanguageDisplay";
  /**
   * Language.
   */
  language: string;
}

export interface CollectionTranslationDetails_collection_translation {
  __typename: "CollectionTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  descriptionJson: any;
  /**
   * Translation's language
   */
  language: CollectionTranslationDetails_collection_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CollectionTranslationDetails_collection {
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
  translation: CollectionTranslationDetails_collection_translation | null;
}

export interface CollectionTranslationDetails {
  /**
   * Lookup a collection by ID.
   */
  collection: CollectionTranslationDetails_collection | null;
}

export interface CollectionTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
