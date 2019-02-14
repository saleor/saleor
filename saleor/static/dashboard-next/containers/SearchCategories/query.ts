import gql from "graphql-tag";

import { TypedQuery } from "../../queries";
import {
  SearchCategories,
  SearchCategoriesVariables
} from "./types/SearchCategories";

export const searchCategories = gql`
  query SearchCategories($query: String!) {
    categories(first: 5, query: $query) {
      edges {
        node {
          id
          name
        }
      }
    }
  }
`;
export const TypedSearchCategoriesQuery = TypedQuery<
  SearchCategories,
  SearchCategoriesVariables
>(searchCategories);
