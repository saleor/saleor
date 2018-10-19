import gql from "graphql-tag";

import { TypedMutation } from "../mutations";
import { collectionDetailsFragment } from "./queries";
import {
  AssignHomepageCollection,
  AssignHomepageCollectionVariables
} from "./types/AssignHomepageCollection";
import {
  CollectionAssignProduct,
  CollectionAssignProductVariables
} from "./types/CollectionAssignProduct";
import {
  CollectionUpdate,
  CollectionUpdateVariables
} from "./types/CollectionUpdate";
import {
  CreateCollection,
  CreateCollectionVariables
} from "./types/CreateCollection";

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

const assignHomepageCollection = gql`
  mutation AssignHomepageCollection($id: ID) {
    homepageCollectionUpdate(collection: $id) {
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
  }
`;
export const TypedAssignHomepageCollectionMutation = TypedMutation<
  AssignHomepageCollection,
  AssignHomepageCollectionVariables
>(assignHomepageCollection);

const assignCollectionProduct = gql`
  mutation CollectionAssignProduct($collectionId: ID!, $productId: ID!) {
    collectionAddProducts(collectionId: $collectionId, products: [$productId]) {
      errors {
        field
        message
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
  mutation CreateCollection($input: CollectionInput!) {
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
