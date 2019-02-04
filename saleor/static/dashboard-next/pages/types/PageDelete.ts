/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: PageDelete
// ====================================================

export interface PageDelete_pageDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface PageDelete_pageDelete {
  __typename: "PageDelete";
  errors: PageDelete_pageDelete_errors[] | null;
}

export interface PageDelete {
  pageDelete: PageDelete_pageDelete | null;
}

export interface PageDeleteVariables {
  id: string;
}
