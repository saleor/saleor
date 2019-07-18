/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: MenuBulkDelete
// ====================================================

export interface MenuBulkDelete_menuBulkDelete_errors {
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

export interface MenuBulkDelete_menuBulkDelete {
  __typename: "MenuBulkDelete";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: MenuBulkDelete_menuBulkDelete_errors[] | null;
}

export interface MenuBulkDelete {
  /**
   * Deletes menus.
   */
  menuBulkDelete: MenuBulkDelete_menuBulkDelete | null;
}

export interface MenuBulkDeleteVariables {
  ids: (string | null)[];
}
