import gql from "graphql-tag";

import { TypedQuery } from "../../queries";
import {
  SearchCollections,
  SearchCollectionsVariables
} from "./types/SearchCollections";

export const searchCollections = gql`
  query SearchCollections($query: String!) {
    collections(first: 5, query: $query) {
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;
export const TypedSearchCollectionsQuery = TypedQuery<
  SearchCollections,
  SearchCollectionsVariables
>(searchCollections);
