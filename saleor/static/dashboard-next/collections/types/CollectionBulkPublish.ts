/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CollectionBulkPublish
// ====================================================

export interface CollectionBulkPublish_collectionBulkPublish_errors {
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

export interface CollectionBulkPublish_collectionBulkPublish {
  __typename: "CollectionBulkPublish";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: CollectionBulkPublish_collectionBulkPublish_errors[] | null;
}

export interface CollectionBulkPublish {
  /**
   * Publish collections.
   */
  collectionBulkPublish: CollectionBulkPublish_collectionBulkPublish | null;
}

export interface CollectionBulkPublishVariables {
  ids: (string | null)[];
  isPublished: boolean;
}
