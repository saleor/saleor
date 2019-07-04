import gql from "graphql-tag";

import BaseSearch from "../BaseSearch";
import {
  SearchCollections,
  SearchCollectionsVariables
} from "./types/SearchCollections";

export const searchCollections = gql`
  query SearchCollections($after: String, $first: Int!, $query: String!) {
    collections(after: $after, first: $first, query: $query) {
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;

export default BaseSearch<SearchCollections, SearchCollectionsVariables>(
  searchCollections
);
