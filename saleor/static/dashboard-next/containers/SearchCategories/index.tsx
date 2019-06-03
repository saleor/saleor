import gql from "graphql-tag";

import BaseSearch from "../BaseSearch";
import {
  SearchCategories,
  SearchCategoriesVariables
} from "./types/SearchCategories";

export const searchCategories = gql`
  query SearchCategories($after: String, $first: Int!, $query: String!) {
    categories(after: $after, first: $first, query: $query) {
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;

export default BaseSearch<SearchCategories, SearchCategoriesVariables>(
  searchCategories
);
