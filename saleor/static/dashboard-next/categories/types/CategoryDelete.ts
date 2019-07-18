/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CategoryDelete
// ====================================================

export interface CategoryDelete_categoryDelete_errors {
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

export interface CategoryDelete_categoryDelete {
  __typename: "CategoryDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: CategoryDelete_categoryDelete_errors[] | null;
}

export interface CategoryDelete {
  /**
   * Deletes a category.
   */
  categoryDelete: CategoryDelete_categoryDelete | null;
}

export interface CategoryDeleteVariables {
  id: string;
}
