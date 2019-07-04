/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CollectionBulkDelete
// ====================================================

export interface CollectionBulkDelete_collectionBulkDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CollectionBulkDelete_collectionBulkDelete {
  __typename: "CollectionBulkDelete";
  errors: CollectionBulkDelete_collectionBulkDelete_errors[] | null;
}

export interface CollectionBulkDelete {
  collectionBulkDelete: CollectionBulkDelete_collectionBulkDelete | null;
}

export interface CollectionBulkDeleteVariables {
  ids: (string | null)[];
}
