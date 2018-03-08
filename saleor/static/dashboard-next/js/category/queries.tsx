import gql from "graphql-tag";
import * as React from "react";
import { Query, QueryProps } from "react-apollo";

import {
  CategoryDetailsQuery,
  CategoryDetailsQueryVariables
} from "./gql-types";

const createTypedQuery = <TData, TVariables>(query) => ({
  children,
  ...other
}) => {
  const TypedQuery = Query as React.ComponentType<
    QueryProps<TData, TVariables>
  >;
  return (
    <TypedQuery query={query} {...other}>
      {children}
    </TypedQuery>
  );
};

export const categoryChildren = gql`
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

export const rootCategoryChildren = gql`
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
