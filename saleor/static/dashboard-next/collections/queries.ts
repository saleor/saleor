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
      url
    }
    seoDescription
    seoTitle
    isPublished
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
          cursor
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
