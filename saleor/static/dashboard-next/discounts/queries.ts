import gql from "graphql-tag";

import { pageInfoFragment, TypedQuery } from "../queries";
import { SaleList, SaleListVariables } from "./types/SaleList";
import { VoucherList, VoucherListVariables } from "./types/VoucherList";

export const saleList = gql`
  ${pageInfoFragment}
  query SaleList($after: String, $before: String, $first: Int, $last: Int) {
    sales(after: $after, before: $before, first: $first, last: $last) {
      edges {
        node {
          id
          name
          type
          startDate
          endDate
          value
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const TypedSaleList = TypedQuery<SaleList, SaleListVariables>(saleList);

export const voucherList = gql`
  ${pageInfoFragment}
  query VoucherList($after: String, $before: String, $first: Int, $last: Int) {
    vouchers(after: $after, before: $before, first: $first, last: $last) {
      edges {
        node {
          id
          name
          startDate
          endDate
          usageLimit
          discountValueType
          discountValue
          minAmountSpent {
            currency
            amount
          }
        }
      }
      pageInfo {
        ...PageInfoFragment
      }
    }
  }
`;
export const TypedVoucherList = TypedQuery<VoucherList, VoucherListVariables>(
  voucherList
);

export const saleDetails = gql`
  ${pageInfoFragment}
  query SaleDetails(
    $id: ID!
    $after: String
    $before: String
    $first: Int
    $last: Int
  ) {
    sale(id: $id) {
      id
      name
      type
      value
      products(after: $after, before: $before, first: $first, last: $last) {
        edges {
          node {
            id
            name
            isPublished
            productType {
              id
              name
            }
            thumbnail {
              url
            }
          }
        }
        pageInfo {
          ...PageInfoFragment
        }
      }
      categories(after: $after, before: $before, first: $first, last: $last) {
        edges {
          node {
            id
            name
            products {
              totalCount
            }
          }
        }
        pageInfo {
          ...PageInfoFragment
        }
      }
      collections(after: $after, before: $before, first: $first, last: $last) {
        edges {
          node {
            id
            name
            products {
              totalCount
            }
          }
        }
        pageInfo {
          ...PageInfoFragment
        }
      }
      startDate
      endDate
    }
  }
`;
