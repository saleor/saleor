/* tslint:disable */
// This file was automatically generated and should not be edited.

// ====================================================
// GraphQL mutation operation: AssignHomepageCollection
// ====================================================

export interface AssignHomepageCollection_homepageCollectionUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface AssignHomepageCollection_homepageCollectionUpdate_shop_homepageCollection {
  __typename: "Collection";
  id: string;
}

export interface AssignHomepageCollection_homepageCollectionUpdate_shop {
  __typename: "Shop";
  homepageCollection: AssignHomepageCollection_homepageCollectionUpdate_shop_homepageCollection | null;
}

export interface AssignHomepageCollection_homepageCollectionUpdate {
  __typename: "HomepageCollectionUpdate";
  errors: AssignHomepageCollection_homepageCollectionUpdate_errors[] | null;
  shop: AssignHomepageCollection_homepageCollectionUpdate_shop | null;
}

export interface AssignHomepageCollection {
  homepageCollectionUpdate: AssignHomepageCollection_homepageCollectionUpdate | null;
}

export interface AssignHomepageCollectionVariables {
  id?: string | null;
}
