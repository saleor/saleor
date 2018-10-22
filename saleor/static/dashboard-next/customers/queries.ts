import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import {
  CustomerDetails,
  CustomerDetailsVariables
} from "./types/CustomerDetails";
import { ListCustomers, ListCustomersVariables } from "./types/ListCustomers";
import { fragmentAddress } from "../orders/queries";

const customerList = gql`
  query ListCustomers(
    $after: String
    $before: String
    $first: Int
    $last: Int
  ) {
    customers(after: $after, before: $before, first: $first, last: $last) {
      edges {
        node {
          email
          id
          orders {
            totalCount
          }
        }
      }
      pageInfo {
        endCursor
        hasNextPage
        hasPreviousPage
        startCursor
      }
    }
  }
`;
export const TypedCustomerListQuery = TypedQuery<
  ListCustomers,
  ListCustomersVariables
>(customerList);

const customerDetails = gql`
  ${fragmentAddress}
  query CustomerDetails($id: ID!, $lastOrders: Int!) {
    user(id: $id) {
      defaultBillingAddress {
        ...AddressFragment
      }
      defaultShippingAddress {
        ...AddressFragment
      }
      email
      id
      isActive
      note
      orders(last: $lastOrders) {
        edges {
          node {
            created
            id
            number
            total {
              gross {
                amount
                currency
              }
            }
          }
        }
      }
    }
  }
`;
export const TypedCustomerDetailsQuery = TypedQuery<
  CustomerDetails,
  CustomerDetailsVariables
>(customerDetails);
