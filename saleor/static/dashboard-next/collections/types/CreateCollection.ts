/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { CollectionCreateInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: CreateCollection
// ====================================================

export interface CreateCollection_collectionCreate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CreateCollection_collectionCreate_collection_backgroundImage {
  __typename: "Image";
  alt: string | null;
  url: string;
}

export interface CreateCollection_collectionCreate_collection {
  __typename: "Collection";
  id: string;
  isPublished: boolean;
  name: string;
  backgroundImage: CreateCollection_collectionCreate_collection_backgroundImage | null;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CreateCollection_collectionCreate {
  __typename: "CollectionCreate";
  errors: CreateCollection_collectionCreate_errors[] | null;
  collection: CreateCollection_collectionCreate_collection | null;
}

export interface CreateCollection {
  collectionCreate: CreateCollection_collectionCreate | null;
}

export interface CreateCollectionVariables {
  input: CollectionCreateInput;
}
