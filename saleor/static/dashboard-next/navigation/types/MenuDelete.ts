/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: MenuDelete
// ====================================================

export interface MenuDelete_menuDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface MenuDelete_menuDelete {
  __typename: "MenuDelete";
  errors: MenuDelete_menuDelete_errors[] | null;
}

export interface MenuDelete {
  menuDelete: MenuDelete_menuDelete | null;
}

export interface MenuDeleteVariables {
  id: string;
}
