import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import { Home } from "./types/Home";

const home = gql`
  query Home {
    salesToday: ordersTotal(period: TODAY) {
      gross {
        amount
        currency
      }
    }
    ordersToday: orders(created: TODAY) {
      totalCount
    }
    ordersToFulfill: orders(status: READY_TO_FULFILL) {
      totalCount
    }
    ordersToCapture: orders(status: READY_TO_CAPTURE) {
      totalCount
    }
    productsOutOfStock: products(stockAvailability: OUT_OF_STOCK) {
      totalCount
    }
    productTopToday: reportProductSales(period: TODAY, first: 5) {
      edges {
        node {
          id
          revenue(period: TODAY) {
            gross {
              amount
              currency
            }
          }
          attributes {
            value {
              id
              name
            }
          }
          product {
            id
            name
            thumbnail {
              url
            }
          }
          quantityOrdered
        }
      }
    }
    activities: homepageEvents(last: 10) {
      edges {
        node {
          amount
          composedId
          date
          email
          emailType
          id
          message
          orderNumber
          oversoldItems
          quantity
          type
          user {
            id
            email
          }
        }
      }
    }
  }
`;
export const HomePageQuery = TypedQuery<Home, {}>(home);
