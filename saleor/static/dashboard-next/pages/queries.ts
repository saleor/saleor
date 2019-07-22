import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import { PageDetails, PageDetailsVariables } from "./types/PageDetails";
import { PageList, PageListVariables } from "./types/PageList";

export const pageFragment = gql`
  fragment PageFragment on Page {
    id
    title
    slug
    isPublished
  }
`;

export const pageDetailsFragment = gql`
  ${pageFragment}
  fragment PageDetailsFragment on Page {
    ...PageFragment
    contentJson
    seoTitle
    seoDescription
    publicationDate
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
export const TypedPageListQuery = TypedQuery<PageList, PageListVariables>(
  pageList
);

const pageDetails = gql`
  ${pageDetailsFragment}
  query PageDetails($id: ID!) {
    page(id: $id) {
      ...PageDetailsFragment
    }
  }
`;
export const TypedPageDetailsQuery = TypedQuery<
  PageDetails,
  PageDetailsVariables
>(pageDetails);
