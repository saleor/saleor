import gql from "graphql-tag";
import { Query, QueryProps } from "react-apollo";

import { PageDetails, PageDetailsVariables } from "./types/PageDetails";
import { PageList, PageListVariables } from "./types/PageList";

export const TypedPageListQuery = Query as React.ComponentType<
  QueryProps<PageList, PageListVariables>
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
  QueryProps<PageDetails, PageDetailsVariables>
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
