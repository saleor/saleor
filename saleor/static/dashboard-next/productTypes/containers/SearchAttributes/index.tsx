import gql from "graphql-tag";

import { pageInfoFragment } from "@saleor/queries";
import BaseSearch from "../../../containers/BaseSearch";
import {
  SearchAttributes,
  SearchAttributesVariables
} from "./types/SearchAttributes";

export const searchAttributes = gql`
  ${pageInfoFragment}
  query SearchAttributes(
    $id: ID!
    $after: String
    $first: Int!
    $query: String!
  ) {
    productType(id: $id) {
      id
      availableAttributes(
        after: $after
        first: $first
        filter: { search: $query }
      ) {
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
  }
`;

export default BaseSearch<SearchAttributes, SearchAttributesVariables>(
  searchAttributes
);
