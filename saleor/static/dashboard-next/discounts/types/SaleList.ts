/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { SaleType } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: SaleList
// ====================================================

export interface SaleList_sales_edges_node {
  __typename: "Sale";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  type: SaleType;
  startDate: any;
  endDate: any | null;
  value: number;
}

export interface SaleList_sales_edges {
  __typename: "SaleCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: SaleList_sales_edges_node;
}

export interface SaleList_sales_pageInfo {
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

export interface SaleList_sales {
  __typename: "SaleCountableConnection";
  edges: SaleList_sales_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: SaleList_sales_pageInfo;
}

export interface SaleList {
  /**
   * List of the shop's sales.
   */
  sales: SaleList_sales | null;
}

export interface SaleListVariables {
  after?: string | null;
  before?: string | null;
  first?: number | null;
  last?: number | null;
}
