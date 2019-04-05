/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: CollectionTranslationDetails
// ====================================================

export interface CollectionTranslationDetails_collection_translation_language {
  __typename: "LanguageDisplay";
  language: string;
}

export interface CollectionTranslationDetails_collection_translation {
  __typename: "CollectionTranslation";
  id: string;
  descriptionJson: any;
  language: CollectionTranslationDetails_collection_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CollectionTranslationDetails_collection {
  __typename: "Collection";
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  translation: CollectionTranslationDetails_collection_translation | null;
}

export interface CollectionTranslationDetails {
  collection: CollectionTranslationDetails_collection | null;
}

export interface CollectionTranslationDetailsVariables {
  id: string;
  language: LanguageCodeEnum;
}
