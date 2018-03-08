import gql from "graphql-tag";
import * as React from "react";
import { Query, QueryProps } from "react-apollo";

import {
  CategoryChildrenQuery,
  CategoryChildrenQueryVariables,
  CategoryDetailsQuery,
  CategoryDetailsQueryVariables,
  RootCategoryChildrenQuery,
  RootCategoryChildrenQueryVariables
} from "./gql-types";

export const categoryChildrenQuery = gql`
  query CategoryChildren(
    $id: ID!
    $first: Int
    $after: String
    $last: Int
    $before: String
  ) {
    category(id: $id) {
      id
      children(first: $first, after: $after, last: $last, before: $before) {
        edges {
          cursor
          node {
            id
            name
            description
          }
        }
        pageInfo {
          hasNextPage
          hasPreviousPage
          startCursor
          endCursor
        }
      }
    }
  }
`;

export const TypedCategoryChildrenQuery = Query as React.ComponentType<
  QueryProps<CategoryChildrenQuery, CategoryChildrenQueryVariables>
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
      products {
        totalCount
      }
    }
  }
`;

export const TypedCategoryDetailsQuery = Query as React.ComponentType<
  QueryProps<CategoryDetailsQuery, CategoryDetailsQueryVariables>
>;

export const rootCategoryChildrenQuery = gql`
  query RootCategoryChildren(
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
        cursor
        node {
          id
          name
          description
        }
      }
      pageInfo {
        hasNextPage
        hasPreviousPage
        startCursor
        endCursor
      }
    }
  }
`;

export const TypedRootCategoryChildrenQuery = Query as React.ComponentType<
  QueryProps<RootCategoryChildrenQuery, RootCategoryChildrenQueryVariables>
>;
