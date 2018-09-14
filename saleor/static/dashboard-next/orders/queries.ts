import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import { OrderDetails, OrderDetailsVariables } from "./types/OrderDetails";
import { OrderList, OrderListVariables } from "./types/OrderList";
import { OrderShippingMethods } from "./types/OrderShippingMethods";
import {
  OrderVariantSearch,
  OrderVariantSearchVariables
} from "./types/OrderVariantSearch";

export const orderListQuery = gql`
  query OrderList($first: Int, $after: String, $last: Int, $before: String) {
    orders(before: $before, after: $after, first: $first, last: $last) {
      edges {
        cursor
        node {
          id
          number
          created
          paymentStatus
          status
          total {
            gross {
              amount
              currency
            }
          }
          userEmail
        }
      }
      pageInfo {
        hasPreviousPage
        hasNextPage
        startCursor
        endCursor
      }
    }
  }
`;
export const TypedOrderListQuery = TypedQuery<OrderList, OrderListVariables>(
  orderListQuery
);

export const fragmentOrderDetails = gql`
  fragment OrderDetailsFragment on Order {
    id
    billingAddress {
      id
      city
      cityArea
      companyName
      country
      countryArea
      firstName
      lastName
      phone
      postalCode
      streetAddress1
      streetAddress2
    }
    created
    events {
      id
      amount
      date
      email
      emailType
      message
      quantity
      type
      user {
        email
      }
    }
    fulfillments {
      id
      lines {
        edges {
          node {
            id
            orderLine {
              id
              productName
            }
            quantity
          }
        }
      }
      status
      trackingNumber
    }
    lines {
      edges {
        node {
          id
          productName
          productSku
          quantity
          quantityFulfilled
          unitPrice {
            gross {
              amount
              currency
            }
            net {
              amount
              currency
            }
          }
        }
      }
    }
    number
    paymentStatus
    shippingAddress {
      id
      city
      cityArea
      companyName
      country
      countryArea
      firstName
      lastName
      phone
      postalCode
      streetAddress1
      streetAddress2
    }
    shippingMethod {
      id
    }
    shippingMethodName
    shippingPrice {
      gross {
        amount
        currency
      }
    }
    status
    subtotal {
      gross {
        amount
        currency
      }
    }
    total {
      gross {
        amount
        currency
      }
      tax {
        amount
        currency
      }
    }
    totalAuthorized {
      amount
      currency
    }
    totalCaptured {
      amount
      currency
    }
    user {
      id
      email
    }
  }
`;

export const orderDetailsQuery = gql`
  ${fragmentOrderDetails}
  query OrderDetails($id: ID!) {
    order(id: $id) {
      ...OrderDetailsFragment
    }
  }
`;
export const TypedOrderDetailsQuery = TypedQuery<
  OrderDetails,
  OrderDetailsVariables
>(orderDetailsQuery);

export const orderShippingMethodsQuery = gql`
  query OrderShippingMethods {
    shippingZones {
      edges {
        node {
          shippingMethods {
            edges {
              node {
                id
                name
              }
            }
          }
        }
      }
    }
  }
`;
export const TypedOrderShippingMethodsQuery = TypedQuery<
  OrderShippingMethods,
  {}
>(orderShippingMethodsQuery);

export const orderVariantSearchQuery = gql`
  query OrderVariantSearch($search: String!) {
    products(query: $search, first: 20) {
      edges {
        node {
          id
          name
          variants {
            edges {
              node {
                id
                name
                sku
                stockQuantity
              }
            }
          }
        }
      }
    }
  }
`;
export const TypedOrderVariantSearch = TypedQuery<
  OrderVariantSearch,
  OrderVariantSearchVariables
>(orderVariantSearchQuery);
