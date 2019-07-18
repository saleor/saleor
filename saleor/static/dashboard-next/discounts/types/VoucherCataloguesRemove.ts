/* tslint:disable */
/* eslint-disable */
// This file was automatically generated and should not be edited.

import { CatalogueInput, DiscountValueTypeEnum, VoucherTypeEnum } from "./../../types/globalTypes";

// ====================================================
// GraphQL mutation operation: VoucherCataloguesRemove
// ====================================================

export interface VoucherCataloguesRemove_voucherCataloguesRemove_errors {
  __typename: "Error";
  /**
   * Name of a field that caused the error. A value of
   *         `null` indicates that the error isn't associated with a particular
   *         field.
   */
  field: string | null;
  /**
   * The error message.
   */
  message: string | null;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_countries {
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

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_minAmountSpent {
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

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products_edges_node_productType {
  __typename: "ProductType";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products_edges_node_thumbnail {
  __typename: "Image";
  /**
   * The URL of the image.
   */
  url: string;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products_edges_node {
  __typename: "Product";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  productType: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products_edges_node_productType;
  isPublished: boolean;
  /**
   * The main thumbnail for a product.
   */
  thumbnail: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products_edges_node_thumbnail | null;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products_edges {
  __typename: "ProductCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products_edges_node;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products_pageInfo {
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

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products {
  __typename: "ProductCountableConnection";
  edges: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products_edges[];
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
  /**
   * Pagination data for this connection.
   */
  pageInfo: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products_pageInfo;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_collections_edges_node_products {
  __typename: "ProductCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_collections_edges_node {
  __typename: "Collection";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * List of products in this collection.
   */
  products: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_collections_edges_node_products | null;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_collections_edges {
  __typename: "CollectionCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_collections_edges_node;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_collections_pageInfo {
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

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_collections {
  __typename: "CollectionCountableConnection";
  edges: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_collections_edges[];
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
  /**
   * Pagination data for this connection.
   */
  pageInfo: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_collections_pageInfo;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_categories_edges_node_products {
  __typename: "ProductCountableConnection";
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_categories_edges_node {
  __typename: "Category";
  /**
   * The ID of the object.
   */
  id: string;
  name: string;
  /**
   * List of products in the category.
   */
  products: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_categories_edges_node_products | null;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_categories_edges {
  __typename: "CategoryCountableEdge";
  /**
   * The item at the end of the edge
   */
  node: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_categories_edges_node;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_categories_pageInfo {
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

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher_categories {
  __typename: "CategoryCountableConnection";
  edges: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_categories_edges[];
  /**
   * A total count of items in the collection
   */
  totalCount: number | null;
  /**
   * Pagination data for this connection.
   */
  pageInfo: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_categories_pageInfo;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove_voucher {
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
  countries: (VoucherCataloguesRemove_voucherCataloguesRemove_voucher_countries | null)[] | null;
  minAmountSpent: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_minAmountSpent | null;
  /**
   * Determines a type of voucher
   */
  type: VoucherTypeEnum;
  used: number;
  applyOncePerOrder: boolean;
  /**
   * List of products this voucher applies to.
   */
  products: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_products | null;
  /**
   * List of collections this voucher applies to.
   */
  collections: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_collections | null;
  /**
   * List of categories this voucher applies to.
   */
  categories: VoucherCataloguesRemove_voucherCataloguesRemove_voucher_categories | null;
}

export interface VoucherCataloguesRemove_voucherCataloguesRemove {
  __typename: "VoucherRemoveCatalogues";
  /**
   * List of errors that occurred executing the mutation.
   */
  errors: VoucherCataloguesRemove_voucherCataloguesRemove_errors[] | null;
  /**
   * Voucher of which catalogue IDs will be modified.
   */
  voucher: VoucherCataloguesRemove_voucherCataloguesRemove_voucher | null;
}

export interface VoucherCataloguesRemove {
  /**
   * Removes products, categories, collections from a voucher.
   */
  voucherCataloguesRemove: VoucherCataloguesRemove_voucherCataloguesRemove | null;
}

export interface VoucherCataloguesRemoveVariables {
  input: CatalogueInput;
  id: string;
  after?: string | null;
  before?: string | null;
  first?: number | null;
  last?: number | null;
}
