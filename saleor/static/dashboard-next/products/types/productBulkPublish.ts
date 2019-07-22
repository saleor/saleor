/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: productBulkPublish
// ====================================================

export interface productBulkPublish_productBulkPublish_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface productBulkPublish_productBulkPublish {
  __typename: "ProductBulkPublish";
  errors: productBulkPublish_productBulkPublish_errors[] | null;
}

export interface productBulkPublish {
  productBulkPublish: productBulkPublish_productBulkPublish | null;
}

export interface productBulkPublishVariables {
  ids: string[];
  isPublished: boolean;
}
