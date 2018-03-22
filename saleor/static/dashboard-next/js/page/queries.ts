import gql from "graphql-tag";
import { Query, QueryProps } from "react-apollo";

import {
  PageDetailsQuery,
  PageDetailsQueryVariables,
  PageListQuery,
  PageListQueryVariables
} from "../gql-types";

export const TypedPageListQuery = Query as React.ComponentType<
  QueryProps<PageListQuery, PageListQueryVariables>
>;
export const pageListQuery = gql`
  query PageList($first: Int, $after: String, $last: Int, $before: String) {
    pages(before: $before, after: $after, first: $first, last: $last) {
      edges {
        cursor
        node {
          id
          slug
          title
          isVisible
        }
      }
      pageInfo {
        hasPreviousPage
        hasNextPage
        startCursor
        endCursor
      }
    }
  }
`;

export const TypedPageDetailsQuery = Query as React.ComponentType<
  QueryProps<PageDetailsQuery, PageDetailsQueryVariables>
>;
export const pageDetailsQuery = gql`
  query PageDetails($id: ID!) {
    page(id: $id) {
      id
      slug
      title
      content
      created
      isVisible
      availableOn
    }
  }
`;
