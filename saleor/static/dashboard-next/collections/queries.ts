import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import {
  CollectionDetails,
  CollectionDetailsVariables
} from "./types/CollectionDetails";
import {
  CollectionList,
  CollectionListVariables
} from "./types/CollectionList";

export const collectionFragment = gql`
  fragment CollectionFragment on Collection {
    id
    isPublished
    name
  }
`;

export const collectionDetailsFragment = gql`
  ${collectionFragment}
  fragment CollectionDetailsFragment on Collection {
    ...CollectionFragment
    backgroundImage {
      alt
      url
    }
    descriptionJson
    seoDescription
    seoTitle
    isPublished
  }
`;

// This fragment is used to make sure that product's fields that are returned
// are always the same - fixes apollo cache
// https://github.com/apollographql/apollo-client/issues/2496
// https://github.com/apollographql/apollo-client/issues/3468
export const collectionProductFragment = gql`
  fragment CollectionProductFragment on Product {
    id
    isPublished
    name
    productType {
      id
      name
    }
    thumbnail {
      url
    }
  }
`;

export const collectionList = gql`
  ${collectionFragment}
  query CollectionList(
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    collections(first: $first, after: $after, before: $before, last: $last) {
      edges {
        node {
          ...CollectionFragment
          products {
            totalCount
          }
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
`;
export const TypedCollectionListQuery = TypedQuery<
  CollectionList,
  CollectionListVariables
>(collectionList);

export const collectionDetails = gql`
  ${collectionDetailsFragment}
  ${collectionProductFragment}
  query CollectionDetails(
    $id: ID!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    collection(id: $id) {
      ...CollectionDetailsFragment
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
    shop {
      homepageCollection {
        id
      }
    }
  }
`;
export const TypedCollectionDetailsQuery = TypedQuery<
  CollectionDetails,
  CollectionDetailsVariables
>(collectionDetails);
