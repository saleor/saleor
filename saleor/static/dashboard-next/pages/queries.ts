import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import { PageList, PageListVariables } from "./types/PageList";

export const pageFragment = gql`
  fragment PageFragment on Page {
    id
    title
    slug
    isVisible
  }
`;

const pageList = gql`
  ${pageFragment}
  query PageList($first: Int, $after: String, $last: Int, $before: String) {
    pages(before: $before, after: $after, first: $first, last: $last) {
      edges {
        node {
          ...PageFragment
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
export const TypedPageList = TypedQuery<PageList, PageListVariables>(pageList);
