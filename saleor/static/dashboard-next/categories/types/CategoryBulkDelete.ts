/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CategoryBulkDelete
// ====================================================

export interface CategoryBulkDelete_categoryBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CategoryBulkDelete_categoryBulkDelete {
  __typename: "CategoryBulkDelete";
  errors: CategoryBulkDelete_categoryBulkDelete_errors[] | null;
}

export interface CategoryBulkDelete {
  categoryBulkDelete: CategoryBulkDelete_categoryBulkDelete | null;
}

export interface CategoryBulkDeleteVariables {
  ids: (string | null)[];
}
