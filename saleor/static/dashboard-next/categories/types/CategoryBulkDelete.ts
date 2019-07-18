/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CategoryBulkDelete
// ====================================================

export interface CategoryBulkDelete_categoryBulkDelete_errors {
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

export interface CategoryBulkDelete_categoryBulkDelete {
  __typename: "CategoryBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: CategoryBulkDelete_categoryBulkDelete_errors[] | null;
}

export interface CategoryBulkDelete {
  /**
   * Deletes categories.
   */
  categoryBulkDelete: CategoryBulkDelete_categoryBulkDelete | null;
}

export interface CategoryBulkDeleteVariables {
  ids: (string | null)[];
}
