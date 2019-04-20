/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { VoucherDiscountValueType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: VoucherList
// ====================================================

export interface VoucherList_vouchers_edges_node_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface VoucherList_vouchers_edges_node_minAmountSpent {
  __typename: "Money";
  currency: string;
  amount: number;
}

export interface VoucherList_vouchers_edges_node {
  __typename: "Voucher";
  id: string;
  name: string | null;
  startDate: any;
  endDate: any | null;
  usageLimit: number | null;
  discountValueType: VoucherDiscountValueType;
  discountValue: number;
  countries: (VoucherList_vouchers_edges_node_countries | null)[] | null;
  minAmountSpent: VoucherList_vouchers_edges_node_minAmountSpent | null;
}

export interface VoucherList_vouchers_edges {
  __typename: "VoucherCountableEdge";
  node: VoucherList_vouchers_edges_node;
}

export interface VoucherList_vouchers_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface VoucherList_vouchers {
  __typename: "VoucherCountableConnection";
  edges: VoucherList_vouchers_edges[];
  pageInfo: VoucherList_vouchers_pageInfo;
}

export interface VoucherList {
  vouchers: VoucherList_vouchers | null;
}

export interface VoucherListVariables {
  after?: string | null;
  before?: string | null;
  first?: number | null;
  last?: number | null;
}
