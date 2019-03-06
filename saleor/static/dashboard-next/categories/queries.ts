import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import {
  CategoryDetails,
  CategoryDetailsVariables
} from "./types/CategoryDetails";
import { RootCategories } from "./types/RootCategories";

export const categoryDetailsFragment = gql`
  fragment CategoryDetailsFragment on Category {
    id
    backgroundImage {
      alt
      url
    }
    name
    descriptionJson
    seoDescription
    seoTitle
    parent {
      id
    }
  }
`;

export const rootCategories = gql`
  query RootCategories(
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    categories(
      level: 0
      first: $first
      after: $after
      last: $last
      before: $before
    ) {
      edges {
        node {
          id
          name
          children {
            totalCount
          }
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
export const TypedRootCategoriesQuery = TypedQuery<RootCategories, {}>(
  rootCategories
);

export const categoryDetails = gql`
  ${categoryDetailsFragment}
  query CategoryDetails(
    $id: ID!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    category(id: $id) {
      ...CategoryDetailsFragment
      children(first: 20) {
        edges {
          node {
            id
            name
            children {
              totalCount
            }
            products {
              totalCount
            }
          }
        }
      }
      products(first: $first, after: $after, last: $last, before: $before) {
        pageInfo {
          endCursor
          hasNextPage
          hasPreviousPage
          startCursor
        }
        edges {
          cursor
          node {
            id
            name
            availability {
              available
            }
            thumbnail {
              url
            }
            price {
              amount
              currency
            }
            productType {
              id
              name
            }
          }
        }
      }
    }
  }
`;
export const TypedCategoryDetailsQuery = TypedQuery<
  CategoryDetails,
  CategoryDetailsVariables
>(categoryDetails);
