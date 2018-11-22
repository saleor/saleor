import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import { PageDetails, PageDetailsVariables } from "./types/PageDetails";
import { PageList, PageListVariables } from "./types/PageList";

const pageListQuery = gql`
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
export const TypedPageListQuery = TypedQuery<PageList, PageListVariables>(
  pageListQuery
);

const pageDetailsQuery = gql`
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
export const TypedPageDetailsQuery = TypedQuery<
  PageDetails,
  PageDetailsVariables
>(pageDetailsQuery);
