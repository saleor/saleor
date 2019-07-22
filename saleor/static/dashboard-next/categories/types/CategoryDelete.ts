/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CategoryDelete
// ====================================================

export interface CategoryDelete_categoryDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CategoryDelete_categoryDelete {
  __typename: "CategoryDelete";
  errors: CategoryDelete_categoryDelete_errors[] | null;
}

export interface CategoryDelete {
  categoryDelete: CategoryDelete_categoryDelete | null;
}

export interface CategoryDeleteVariables {
  id: string;
}
