import gql from "graphql-tag";

import BaseSearch from "../BaseSearch";
import {
  SearchAttributes,
  SearchAttributesVariables
} from "./types/SearchAttributes";

export const searchAttributes = gql`
  query SearchAttributes($after: String, $first: Int!, $query: String!) {
    attributes(after: $after, first: $first, query: $query) {
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;

export default BaseSearch<SearchAttributes, SearchAttributesVariables>(
  searchAttributes
);
