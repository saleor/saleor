import gql from "graphql-tag";

import { TypedQuery } from "../queries";
import { SaleList, SaleListVariables } from "./types/SaleList";
import { VoucherList, VoucherListVariables } from "./types/VoucherList";

export const saleList = gql`
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
    }
  }
`;
export const TypedSaleList = TypedQuery<SaleList, SaleListVariables>(saleList);

export const voucherList = gql`
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
    }
  }
`;
export const TypedVoucherList = TypedQuery<VoucherList, VoucherListVariables>(
  voucherList
);
