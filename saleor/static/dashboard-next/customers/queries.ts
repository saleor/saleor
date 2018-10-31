import gql from "graphql-tag";

import { fragmentAddress } from "../orders/queries";
import { TypedQuery } from "../queries";
import { CustomerCreateData } from "./types/CustomerCreateData";
import {
  CustomerDetails,
  CustomerDetailsVariables
} from "./types/CustomerDetails";
import { ListCustomers, ListCustomersVariables } from "./types/ListCustomers";

export const customerFragment = gql`
  fragment CustomerFragment on User {
    id
    email
  }
`;

export const customerDetailsFragment = gql`
  ${customerFragment}
  ${fragmentAddress}
  fragment CustomerDetailsFragment on User {
    ...CustomerFragment
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
  }
`;

const customerList = gql`
  ${customerFragment}
  query ListCustomers(
    $after: String
    $before: String
    $first: Int
    $last: Int
  ) {
    customers(after: $after, before: $before, first: $first, last: $last) {
      edges {
        node {
          ...CustomerFragment
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
  ${customerDetailsFragment}
  query CustomerDetails($id: ID!) {
    user(id: $id) {
      ...CustomerDetailsFragment
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

const customerCreateData = gql`
  query CustomerCreateData {
    shop {
      countries {
        code
        country
      }
    }
  }
`;
export const TypedCustomerCreateDataQuery = TypedQuery<CustomerCreateData, {}>(
  customerCreateData
);
