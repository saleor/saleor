import gql from "graphql-tag";

import { TypedQuery } from "../../queries";
import {
  SearchProducts,
  SearchProductsVariables
} from "./types/SearchProducts";

export const searchProducts = gql`
  query SearchProducts($query: String!) {
    products(first: 5, query: $query) {
      edges {
        node {
          id
          thumbnail {
            url
          }
          name
        }
      }
    }
  }
`;
export const TypedSearchProductsQuery = TypedQuery<
  SearchProducts,
  SearchProductsVariables
>(searchProducts);
