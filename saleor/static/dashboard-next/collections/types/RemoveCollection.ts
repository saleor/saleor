/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: RemoveCollection
// ====================================================

export interface RemoveCollection_collectionDelete_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface RemoveCollection_collectionDelete {
  __typename: "CollectionDelete";
  errors: RemoveCollection_collectionDelete_errors[] | null;
}

export interface RemoveCollection {
  collectionDelete: RemoveCollection_collectionDelete | null;
}

export interface RemoveCollectionVariables {
  id: string;
}
