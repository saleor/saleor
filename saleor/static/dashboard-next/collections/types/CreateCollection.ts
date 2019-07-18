/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { CollectionCreateInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: CreateCollection
// ====================================================

export interface CreateCollection_collectionCreate_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface CreateCollection_collectionCreate_collection_backgroundImage {
  __typename: "Image";
  /**
   * Alt text for an image.
   */
  alt: string | null;
  /**
   * The URL of the image.
   */
  url: string;
}

export interface CreateCollection_collectionCreate_collection {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  isPublished: boolean;
  name: string;
  backgroundImage: CreateCollection_collectionCreate_collection_backgroundImage | null;
  descriptionJson: any;
  publicationDate: any | null;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CreateCollection_collectionCreate {
  __typename: "CollectionCreate";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: CreateCollection_collectionCreate_errors[] | null;
  collection: CreateCollection_collectionCreate_collection | null;
}

export interface CreateCollection {
  /**
   * Creates a new collection.
   */
  collectionCreate: CreateCollection_collectionCreate | null;
}

export interface CreateCollectionVariables {
  input: CollectionCreateInput;
}
