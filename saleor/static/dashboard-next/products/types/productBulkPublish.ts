/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: productBulkPublish
// ====================================================

export interface productBulkPublish_productBulkPublish_errors {
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

export interface productBulkPublish_productBulkPublish {
  __typename: "ProductBulkPublish";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: productBulkPublish_productBulkPublish_errors[] | null;
}

export interface productBulkPublish {
  /**
   * Publish products.
   */
  productBulkPublish: productBulkPublish_productBulkPublish | null;
}

export interface productBulkPublishVariables {
  ids: string[];
  isPublished: boolean;
}
