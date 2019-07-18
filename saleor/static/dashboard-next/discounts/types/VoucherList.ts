/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { DiscountValueTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: VoucherList
// ====================================================

export interface VoucherList_vouchers_edges_node_countries {
  __typename: "CountryDisplay";
  /**
   * Country code.
   */
  code: string;
  /**
   * Country name.
   */
  country: string;
}

export interface VoucherList_vouchers_edges_node_minAmountSpent {
  __typename: "Money";
  /**
   * Currency code.
   */
  currency: string;
  /**
   * Amount of money.
   */
  amount: number;
}

export interface VoucherList_vouchers_edges_node {
  __typename: "Voucher";
  /**
   * The ID of the object.
   */
  id: string;
  code: string;
  startDate: any;
  endDate: any | null;
  usageLimit: number | null;
  /**
   * Determines a type of discount for voucher - value or percentage
   */
  discountValueType: DiscountValueTypeEnum;
  discountValue: number;
  /**
   * List of countries available for the shipping voucher.
   */
  countries: (VoucherList_vouchers_edges_node_countries | null)[] | null;
  minAmountSpent: VoucherList_vouchers_edges_node_minAmountSpent | null;
}

export interface VoucherList_vouchers_edges {
  __typename: "VoucherCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: VoucherList_vouchers_edges_node;
}

export interface VoucherList_vouchers_pageInfo {
  __typename: "PageInfo";
  /**
   * When paginating forwards, the cursor to continue.
   */
  endCursor: string | null;
  /**
   * When paginating forwards, are there more items?
   */
  hasNextPage: boolean;
  /**
   * When paginating backwards, are there more items?
   */
  hasPreviousPage: boolean;
  /**
   * When paginating backwards, the cursor to continue.
   */
  startCursor: string | null;
}

export interface VoucherList_vouchers {
  __typename: "VoucherCountableConnection";
  edges: VoucherList_vouchers_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: VoucherList_vouchers_pageInfo;
}

export interface VoucherList {
  /**
   * List of the shop's vouchers.
   */
  vouchers: VoucherList_vouchers | null;
}

export interface VoucherListVariables {
  after?: string | null;
  before?: string | null;
  first?: number | null;
  last?: number | null;
}
