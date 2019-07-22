/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: PageBulkRemove
// ====================================================

export interface PageBulkRemove_pageBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface PageBulkRemove_pageBulkDelete {
  __typename: "PageBulkDelete";
  errors: PageBulkRemove_pageBulkDelete_errors[] | null;
}

export interface PageBulkRemove {
  pageBulkDelete: PageBulkRemove_pageBulkDelete | null;
}

export interface PageBulkRemoveVariables {
  ids: (string | null)[];
}
