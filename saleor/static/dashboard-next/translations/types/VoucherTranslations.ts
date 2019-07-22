/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { LanguageCodeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL query operation: VoucherTranslations
// ====================================================

export interface VoucherTranslations_vouchers_edges_node_translation_language {
  __typename: "LanguageDisplay";
  code: LanguageCodeEnum;
  language: string;
}

export interface VoucherTranslations_vouchers_edges_node_translation {
  __typename: "VoucherTranslation";
  id: string;
  language: VoucherTranslations_vouchers_edges_node_translation_language;
  name: string | null;
}

export interface VoucherTranslations_vouchers_edges_node {
  __typename: "Voucher";
  id: string;
  name: string | null;
  translation: VoucherTranslations_vouchers_edges_node_translation | null;
}

export interface VoucherTranslations_vouchers_edges {
  __typename: "VoucherCountableEdge";
  node: VoucherTranslations_vouchers_edges_node;
}

export interface VoucherTranslations_vouchers_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface VoucherTranslations_vouchers {
  __typename: "VoucherCountableConnection";
  edges: VoucherTranslations_vouchers_edges[];
  pageInfo: VoucherTranslations_vouchers_pageInfo;
}

export interface VoucherTranslations {
  vouchers: VoucherTranslations_vouchers | null;
}

export interface VoucherTranslationsVariables {
  language: LanguageCodeEnum;
  first?: number | null;
  after?: string | null;
  last?: number | null;
  before?: string | null;
}
