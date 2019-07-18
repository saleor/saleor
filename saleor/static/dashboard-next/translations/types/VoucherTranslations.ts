/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: VoucherTranslations
// ====================================================

export interface VoucherTranslations_vouchers_edges_node_translation_language {
  __typename: "LanguageDisplay";
  /**
   * Language code.
   */
  code: LanguageCodeEnum;
  /**
   * Language.
   */
  language: string;
}

export interface VoucherTranslations_vouchers_edges_node_translation {
  __typename: "VoucherTranslation";
  /**
   * The ID of the object.
   */
  id: string;
  /**
   * Translation's language
   */
  language: VoucherTranslations_vouchers_edges_node_translation_language;
  name: string | null;
}

export interface VoucherTranslations_vouchers_edges_node {
  __typename: "Voucher";
  /**
   * The ID of the object.
   */
  id: string;
  name: string | null;
  /**
   * Returns translated Voucher fields for the given language code.
   */
  translation: VoucherTranslations_vouchers_edges_node_translation | null;
}

export interface VoucherTranslations_vouchers_edges {
  __typename: "VoucherCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: VoucherTranslations_vouchers_edges_node;
}

export interface VoucherTranslations_vouchers_pageInfo {
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

export interface VoucherTranslations_vouchers {
  __typename: "VoucherCountableConnection";
  edges: VoucherTranslations_vouchers_edges[];
  /**
   * Pagination data for this connection.
   */
  pageInfo: VoucherTranslations_vouchers_pageInfo;
}

export interface VoucherTranslations {
  /**
   * List of the shop's vouchers.
   */
  vouchers: VoucherTranslations_vouchers | null;
}

export interface VoucherTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
