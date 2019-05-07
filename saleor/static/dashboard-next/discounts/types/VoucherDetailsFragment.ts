/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { VoucherDiscountValueType, VoucherType } from "./../../types/globalTypes";

// ====================================================
// GraphQL fragment: VoucherDetailsFragment
// ====================================================

export interface VoucherDetailsFragment_countries {
  __typename: "CountryDisplay";
  code: string;
  country: string;
}

export interface VoucherDetailsFragment_minAmountSpent {
  __typename: "Money";
  currency: string;
  amount: number;
}

export interface VoucherDetailsFragment_products_edges_node_productType {
  __typename: "ProductType";
  id: string;
  name: string;
}

export interface VoucherDetailsFragment_products_edges_node_thumbnail {
  __typename: "Image";
  url: string;
}

export interface VoucherDetailsFragment_products_edges_node {
  __typename: "Product";
  id: string;
  name: string;
  productType: VoucherDetailsFragment_products_edges_node_productType;
  isPublished: boolean;
  thumbnail: VoucherDetailsFragment_products_edges_node_thumbnail | null;
}

export interface VoucherDetailsFragment_products_edges {
  __typename: "ProductCountableEdge";
  node: VoucherDetailsFragment_products_edges_node;
}

export interface VoucherDetailsFragment_products_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface VoucherDetailsFragment_products {
  __typename: "ProductCountableConnection";
  edges: VoucherDetailsFragment_products_edges[];
  totalCount: number | null;
  pageInfo: VoucherDetailsFragment_products_pageInfo;
}

export interface VoucherDetailsFragment_collections_edges_node_products {
  __typename: "ProductCountableConnection";
  totalCount: number | null;
}

export interface VoucherDetailsFragment_collections_edges_node {
  __typename: "Collection";
  id: string;
  name: string;
  products: VoucherDetailsFragment_collections_edges_node_products | null;
}

export interface VoucherDetailsFragment_collections_edges {
  __typename: "CollectionCountableEdge";
  node: VoucherDetailsFragment_collections_edges_node;
}

export interface VoucherDetailsFragment_collections_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface VoucherDetailsFragment_collections {
  __typename: "CollectionCountableConnection";
  edges: VoucherDetailsFragment_collections_edges[];
  totalCount: number | null;
  pageInfo: VoucherDetailsFragment_collections_pageInfo;
}

export interface VoucherDetailsFragment_categories_edges_node_products {
  __typename: "ProductCountableConnection";
  totalCount: number | null;
}

export interface VoucherDetailsFragment_categories_edges_node {
  __typename: "Category";
  id: string;
  name: string;
  products: VoucherDetailsFragment_categories_edges_node_products | null;
}

export interface VoucherDetailsFragment_categories_edges {
  __typename: "CategoryCountableEdge";
  node: VoucherDetailsFragment_categories_edges_node;
}

export interface VoucherDetailsFragment_categories_pageInfo {
  __typename: "PageInfo";
  endCursor: string | null;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
}

export interface VoucherDetailsFragment_categories {
  __typename: "CategoryCountableConnection";
  edges: VoucherDetailsFragment_categories_edges[];
  totalCount: number | null;
  pageInfo: VoucherDetailsFragment_categories_pageInfo;
}

export interface VoucherDetailsFragment {
  __typename: "Voucher";
  id: string;
  name: string | null;
  startDate: any;
  endDate: any | null;
  usageLimit: number | null;
  discountValueType: VoucherDiscountValueType;
  discountValue: number;
  countries: (VoucherDetailsFragment_countries | null)[] | null;
  minAmountSpent: VoucherDetailsFragment_minAmountSpent | null;
  type: VoucherType;
  code: string;
  used: number;
  applyOncePerOrder: boolean;
  products: VoucherDetailsFragment_products | null;
  collections: VoucherDetailsFragment_collections | null;
  categories: VoucherDetailsFragment_categories | null;
}
