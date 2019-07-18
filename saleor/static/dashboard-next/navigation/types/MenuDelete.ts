/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: MenuDelete
// ====================================================

export interface MenuDelete_menuDelete_errors {
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

export interface MenuDelete_menuDelete {
  __typename: "MenuDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: MenuDelete_menuDelete_errors[] | null;
}

export interface MenuDelete {
  /**
   * Deletes a menu.
   */
  menuDelete: MenuDelete_menuDelete | null;
}

export interface MenuDeleteVariables {
  id: string;
}
