import gql from "graphql-tag";
import * as React from "react";
import { Query, QueryProps } from "react-apollo";

import {
  CategoryDetailsQuery,
  CategoryDetailsQueryVariables,
  CategoryPropertiesQuery,
  CategoryPropertiesQueryVariables,
  RootCategoryChildrenQuery
} from "../gql-types";

export const TypedCategoryDetailsQuery = Query as React.ComponentType<
  QueryProps<CategoryDetailsQuery, CategoryDetailsQueryVariables>
>;
export const categoryDetailsQuery = gql`
  query CategoryDetails($id: ID!) {
    category(id: $id) {
      id
      name
      description
      parent {
        id
      }
    }
  }
`;

export const TypedRootCategoryChildrenQuery = Query as React.ComponentType<
  QueryProps<RootCategoryChildrenQuery>
>;
export const rootCategoryChildrenQuery = gql`
  query RootCategoryChildren {
    categories(level: 0) {
      edges {
        cursor
        node {
          id
          name
        }
      }
    }
  }
`;

export const TypedCategoryPropertiesQuery = Query as React.ComponentType<
  QueryProps<CategoryPropertiesQuery, CategoryPropertiesQueryVariables>
>;
export const categoryPropertiesQuery = gql`
  query CategoryProperties(
    $id: ID!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    category(id: $id) {
      id
      name
      description
      parent {
        id
      }
      children {
        edges {
          node {
            id
            name
          }
        }
      }
      products(first: $first, after: $after, last: $last, before: $before) {
        totalCount
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
            thumbnailUrl
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
