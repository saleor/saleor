import gql from "graphql-tag";

import BaseSearch from "../BaseSearch";
import {
  SearchCustomers,
  SearchCustomersVariables
} from "./types/SearchCustomers";

export const searchCustomers = gql`
  query SearchCustomers($after: String, $first: Int!, $query: String!) {
    customers(after: $after, first: $first, query: $query) {
      edges {
        node {
          id
          email
        }
      }
    }
  }
`;

export default BaseSearch<SearchCustomers, SearchCustomersVariables>(
  searchCustomers
);
