/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: RemoveCollection
// ====================================================

export interface RemoveCollection_collectionDelete_errors {
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

export interface RemoveCollection_collectionDelete {
  __typename: "CollectionDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: RemoveCollection_collectionDelete_errors[] | null;
}

export interface RemoveCollection {
  /**
   * Deletes a collection.
   */
  collectionDelete: RemoveCollection_collectionDelete | null;
}

export interface RemoveCollectionVariables {
  id: string;
}
