import gql from "graphql-tag";

import BaseSearch from "../BaseSearch";
import {
  SearchProducts,
  SearchProductsVariables
} from "./types/SearchProducts";

export const searchProducts = gql`
  query SearchProducts($after: String, $first: Int!, $query: String!) {
    products(after: $after, first: $first, query: $query) {
      edges {
        node {
          id
          name
          thumbnail {
            url
          }
        }
      }
    }
  }
`;

export default BaseSearch<SearchProducts, SearchProductsVariables>(
  searchProducts
);
