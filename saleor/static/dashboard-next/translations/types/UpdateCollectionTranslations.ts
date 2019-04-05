/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { TranslationInput, LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: UpdateCollectionTranslations
// ====================================================

export interface UpdateCollectionTranslations_collectionTranslate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface UpdateCollectionTranslations_collectionTranslate_collection_translation_language {
  __typename: "LanguageDisplay";
  language: string;
}

export interface UpdateCollectionTranslations_collectionTranslate_collection_translation {
  __typename: "CollectionTranslation";
  id: string;
  descriptionJson: any;
  language: UpdateCollectionTranslations_collectionTranslate_collection_translation_language;
  name: string;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface UpdateCollectionTranslations_collectionTranslate_collection {
  __typename: "Collection";
  id: string;
  name: string;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
  translation: UpdateCollectionTranslations_collectionTranslate_collection_translation | null;
}

export interface UpdateCollectionTranslations_collectionTranslate {
  __typename: "CollectionTranslate";
  errors: UpdateCollectionTranslations_collectionTranslate_errors[] | null;
  collection: UpdateCollectionTranslations_collectionTranslate_collection | null;
}

export interface UpdateCollectionTranslations {
  collectionTranslate: UpdateCollectionTranslations_collectionTranslate | null;
}

export interface UpdateCollectionTranslationsVariables {
  id: string;
  input: TranslationInput;
  language: LanguageCodeEnum;
}
