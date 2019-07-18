/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: PageRemove
// ====================================================

export interface PageRemove_pageDelete_errors {
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

export interface PageRemove_pageDelete {
  __typename: "PageDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: PageRemove_pageDelete_errors[] | null;
}

export interface PageRemove {
  /**
   * Deletes a page.
   */
  pageDelete: PageRemove_pageDelete | null;
}

export interface PageRemoveVariables {
  id: string;
}
