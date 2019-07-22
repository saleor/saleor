import gql from "graphql-tag";

import { pageInfoFragment } from "@saleor/queries";
import BaseSearch from "../BaseSearch";
import {
  SearchAttributes,
  SearchAttributesVariables
} from "./types/SearchAttributes";

export const searchAttributes = gql`
  ${pageInfoFragment}
  query SearchAttributes($after: String, $first: Int!, $query: String!) {
    attributes(after: $after, first: $first, query: $query) {
      edges {
        node {
          id
          name
          slug
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;

export default BaseSearch<SearchAttributes, SearchAttributesVariables>(
  searchAttributes
);
