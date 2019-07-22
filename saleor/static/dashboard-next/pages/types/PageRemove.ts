/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: PageRemove
// ====================================================

export interface PageRemove_pageDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface PageRemove_pageDelete {
  __typename: "PageDelete";
  errors: PageRemove_pageDelete_errors[] | null;
}

export interface PageRemove {
  pageDelete: PageRemove_pageDelete | null;
}

export interface PageRemoveVariables {
  id: string;
}
