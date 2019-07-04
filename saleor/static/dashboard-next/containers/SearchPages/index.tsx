import gql from "graphql-tag";

import BaseSearch from "../BaseSearch";
import { SearchPages, SearchPagesVariables } from "./types/SearchPages";

export const searchPages = gql`
  query SearchPages($after: String, $first: Int!, $query: String!) {
    pages(after: $after, first: $first, query: $query) {
      edges {
        node {
          id
          title
        }
      }
    }
  }
`;

export default BaseSearch<SearchPages, SearchPagesVariables>(searchPages);
