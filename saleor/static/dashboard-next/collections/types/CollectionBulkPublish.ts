/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: CollectionBulkPublish
// ====================================================

export interface CollectionBulkPublish_collectionBulkPublish_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CollectionBulkPublish_collectionBulkPublish {
  __typename: "CollectionBulkPublish";
  errors: CollectionBulkPublish_collectionBulkPublish_errors[] | null;
}

export interface CollectionBulkPublish {
  collectionBulkPublish: CollectionBulkPublish_collectionBulkPublish | null;
}

export interface CollectionBulkPublishVariables {
  ids: (string | null)[];
  isPublished: boolean;
}
