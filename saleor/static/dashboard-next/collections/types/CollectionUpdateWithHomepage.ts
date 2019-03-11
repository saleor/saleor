/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { CollectionInput } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: CollectionUpdateWithHomepage
// ====================================================

export interface CollectionUpdateWithHomepage_homepageCollectionUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CollectionUpdateWithHomepage_homepageCollectionUpdate_shop_homepageCollection {
  __typename: "Collection";
  id: string;
}

export interface CollectionUpdateWithHomepage_homepageCollectionUpdate_shop {
  __typename: "Shop";
  homepageCollection: CollectionUpdateWithHomepage_homepageCollectionUpdate_shop_homepageCollection | null;
}

export interface CollectionUpdateWithHomepage_homepageCollectionUpdate {
  __typename: "HomepageCollectionUpdate";
  errors: CollectionUpdateWithHomepage_homepageCollectionUpdate_errors[] | null;
  shop: CollectionUpdateWithHomepage_homepageCollectionUpdate_shop | null;
}

export interface CollectionUpdateWithHomepage_collectionUpdate_errors {
  __typename: "Error";
  field: string | null;
  message: string | null;
}

export interface CollectionUpdateWithHomepage_collectionUpdate_collection_backgroundImage {
  __typename: "Image";
  alt: string | null;
  url: string;
}

export interface CollectionUpdateWithHomepage_collectionUpdate_collection {
  __typename: "Collection";
  id: string;
  isPublished: boolean;
  name: string;
  backgroundImage: CollectionUpdateWithHomepage_collectionUpdate_collection_backgroundImage | null;
  descriptionJson: any;
  seoDescription: string | null;
  seoTitle: string | null;
}

export interface CollectionUpdateWithHomepage_collectionUpdate {
  __typename: "CollectionUpdate";
  errors: CollectionUpdateWithHomepage_collectionUpdate_errors[] | null;
  collection: CollectionUpdateWithHomepage_collectionUpdate_collection | null;
}

export interface CollectionUpdateWithHomepage {
  homepageCollectionUpdate: CollectionUpdateWithHomepage_homepageCollectionUpdate | null;
  collectionUpdate: CollectionUpdateWithHomepage_collectionUpdate | null;
}

export interface CollectionUpdateWithHomepageVariables {
  id: string;
  input: CollectionInput;
  homepageId?: string | null;
}
