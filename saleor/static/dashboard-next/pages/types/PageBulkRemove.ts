/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: PageBulkRemove
// ====================================================

export interface PageBulkRemove_pageBulkDelete_errors {
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

export interface PageBulkRemove_pageBulkDelete {
  __typename: "PageBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: PageBulkRemove_pageBulkDelete_errors[] | null;
}

export interface PageBulkRemove {
  /**
   * Deletes pages.
   */
  pageBulkDelete: PageBulkRemove_pageBulkDelete | null;
}

export interface PageBulkRemoveVariables {
  ids: (string | null)[];
}
