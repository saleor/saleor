/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: MenuBulkDelete
// ====================================================

export interface MenuBulkDelete_menuBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface MenuBulkDelete_menuBulkDelete {
  __typename: "MenuBulkDelete";
  errors: MenuBulkDelete_menuBulkDelete_errors[] | null;
}

export interface MenuBulkDelete {
  menuBulkDelete: MenuBulkDelete_menuBulkDelete | null;
}

export interface MenuBulkDeleteVariables {
  ids: (string | null)[];
}
