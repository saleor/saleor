import gql from "graphql-tag";

import { TypedQuery } from "../../queries";
import { SearchPages, SearchPagesVariables } from "./types/SearchPages";

export const searchPages = gql`
  query SearchPages($query: String!) {
    pages(first: 5, query: $query) {
      edges {
        node {
          id
          title
        }
      }
    }
  }
`;
export const TypedSearchPagesQuery = TypedQuery<
  SearchPages,
  SearchPagesVariables
>(searchPages);
