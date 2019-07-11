import gql from "graphql-tag";

import { TypedQuery } from "../../../core/queries";
import { SearchResults, SearchResultsVariables } from "./types/SearchResults";

const searchResultsQuery = gql`
  query SearchResults($query: String!) {
    products(query: $query, first: 20) {
      edges {
        node {
          id
          name
          thumbnail {
            url
            alt
          }
          thumbnail2x: thumbnail(size: 510) {
            url
          }
          url
          category {
            id
            name
          }
        }
      }
      pageInfo {
        endCursor
        hasNextPage
        hasPreviousPage
        startCursor
      }
    }
  }
`;

export const TypedSearchResults = TypedQuery<
  SearchResults,
  SearchResultsVariables
>(searchResultsQuery);
