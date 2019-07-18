/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CollectionBulkDelete
// ====================================================

export interface CollectionBulkDelete_collectionBulkDelete_errors {
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

export interface CollectionBulkDelete_collectionBulkDelete {
  __typename: "CollectionBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: CollectionBulkDelete_collectionBulkDelete_errors[] | null;
}

export interface CollectionBulkDelete {
  /**
   * Deletes collections.
   */
  collectionBulkDelete: CollectionBulkDelete_collectionBulkDelete | null;
}

export interface CollectionBulkDeleteVariables {
  ids: (string | null)[];
}
