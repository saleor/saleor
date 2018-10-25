import gql from "graphql-tag";

import { fragmentAddress } from "../orders/queries";
import { TypedQuery } from "../queries";
import {
  CustomerDetails,
  CustomerDetailsVariables
} from "./types/CustomerDetails";
import { ListCustomers, ListCustomersVariables } from "./types/ListCustomers";

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
  query CustomerDetails($id: ID!) {
    user(id: $id) {
      id
      email
      dateJoined
      lastLogin
      defaultShippingAddress {
        ...AddressFragment
      }
      defaultBillingAddress {
        ...AddressFragment
      }
      note
      isActive
      orders(last: 5) {
        edges {
          node {
            id
            created
            number
            paymentStatus
            total {
              gross {
                currency
                amount
              }
            }
          }
        }
      }
      lastPlacedOrder: orders(last: 1) {
        edges {
          node {
            id
            created
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
