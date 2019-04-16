import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import {
  collectionDetailsFragment,
  collectionProductFragment
} from "./queries";
import {
  CollectionAssignProduct,
  CollectionAssignProductVariables
} from "./types/CollectionAssignProduct";
import {
  CollectionBulkDelete,
  CollectionBulkDeleteVariables
} from "./types/CollectionBulkDelete";
import {
  CollectionBulkPublish,
  CollectionBulkPublishVariables
} from "./types/CollectionBulkPublish";
import {
  CollectionUpdate,
  CollectionUpdateVariables
} from "./types/CollectionUpdate";
import {
  CollectionUpdateWithHomepage,
  CollectionUpdateWithHomepageVariables
} from "./types/CollectionUpdateWithHomepage";
import {
  CreateCollection,
  CreateCollectionVariables
} from "./types/CreateCollection";
import {
  RemoveCollection,
  RemoveCollectionVariables
} from "./types/RemoveCollection";
import {
  UnassignCollectionProduct,
  UnassignCollectionProductVariables
} from "./types/UnassignCollectionProduct";

const collectionUpdate = gql`
  ${collectionDetailsFragment}
  mutation CollectionUpdate($id: ID!, $input: CollectionInput!) {
    collectionUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      collection {
        ...CollectionDetailsFragment
      }
    }
  }
`;
export const TypedCollectionUpdateMutation = TypedMutation<
  CollectionUpdate,
  CollectionUpdateVariables
>(collectionUpdate);

const collectionUpdateWithHomepage = gql`
  ${collectionDetailsFragment}
  mutation CollectionUpdateWithHomepage(
    $id: ID!
    $input: CollectionInput!
    $homepageId: ID
  ) {
    homepageCollectionUpdate(collection: $homepageId) {
      errors {
        field
        message
      }
      shop {
        homepageCollection {
          id
        }
      }
    }
    collectionUpdate(id: $id, input: $input) {
      errors {
        field
        message
      }
      collection {
        ...CollectionDetailsFragment
      }
    }
  }
`;
export const TypedCollectionUpdateWithHomepageMutation = TypedMutation<
  CollectionUpdateWithHomepage,
  CollectionUpdateWithHomepageVariables
>(collectionUpdateWithHomepage);

const assignCollectionProduct = gql`
  ${collectionProductFragment}
  mutation CollectionAssignProduct(
    $collectionId: ID!
    $productIds: [ID!]!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    collectionAddProducts(collectionId: $collectionId, products: $productIds) {
      errors {
        field
        message
      }
      collection {
        id
        products(first: $first, after: $after, before: $before, last: $last) {
          edges {
            node {
              ...CollectionProductFragment
            }
          }
          pageInfo {
            endCursor
            hasNextPage
            hasPreviousPage
            startCursor
          }
        }
      }
    }
  }
`;
export const TypedCollectionAssignProductMutation = TypedMutation<
  CollectionAssignProduct,
  CollectionAssignProductVariables
>(assignCollectionProduct);

const createCollection = gql`
  ${collectionDetailsFragment}
  mutation CreateCollection($input: CollectionCreateInput!) {
    collectionCreate(input: $input) {
      errors {
        field
        message
      }
      collection {
        ...CollectionDetailsFragment
      }
    }
  }
`;
export const TypedCollectionCreateMutation = TypedMutation<
  CreateCollection,
  CreateCollectionVariables
>(createCollection);

const removeCollection = gql`
  mutation RemoveCollection($id: ID!) {
    collectionDelete(id: $id) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedCollectionRemoveMutation = TypedMutation<
  RemoveCollection,
  RemoveCollectionVariables
>(removeCollection);

const unassignCollectionProduct = gql`
  mutation UnassignCollectionProduct(
    $collectionId: ID!
    $productIds: [ID]!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    collectionRemoveProducts(
      collectionId: $collectionId
      products: $productIds
    ) {
      errors {
        field
        message
      }
      collection {
        id
        products(first: $first, after: $after, before: $before, last: $last) {
          edges {
            node {
              id
              isPublished
              name
              productType {
                id
                name
              }
              thumbnailUrl
            }
          }
          pageInfo {
            endCursor
            hasNextPage
            hasPreviousPage
            startCursor
          }
        }
      }
    }
  }
`;
export const TypedUnassignCollectionProductMutation = TypedMutation<
  UnassignCollectionProduct,
  UnassignCollectionProductVariables
>(unassignCollectionProduct);

const collectionBulkDelete = gql`
  mutation CollectionBulkDelete($ids: [ID]!) {
    collectionBulkDelete(ids: $ids) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedCollectionBulkDelete = TypedMutation<
  CollectionBulkDelete,
  CollectionBulkDeleteVariables
>(collectionBulkDelete);

const collectionBulkPublish = gql`
  mutation CollectionBulkPublish($ids: [ID]!, $isPublished: Boolean!) {
    collectionBulkPublish(ids: $ids, isPublished: $isPublished) {
      errors {
        field
        message
      }
    }
  }
`;
export const TypedCollectionBulkPublish = TypedMutation<
  CollectionBulkPublish,
  CollectionBulkPublishVariables
>(collectionBulkPublish);
