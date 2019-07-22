import { SearchQueryVariables } from "./containers/BaseSearch";

export const APP_MOUNT_URI = "/dashboard/next/";
export const API_URI = "/graphql/";

export const DEFAULT_INITIAL_SEARCH_DATA: SearchQueryVariables = {
  after: null,
  first: 5,
  query: ""
};

export const PAGINATE_BY = 20;

export const defaultListSettings = {
  CATEGORY_LIST: {
    name: "CATEGORY_LIST",
    rowNumber: PAGINATE_BY
  },
  COLLECTION_LIST: {
    name: "COLLECTION_LIST",
    rowNumber: PAGINATE_BY
  },
  CUSTOMER_LIST: {
    name: "CUSTOMER_LIST",
    rowNumber: PAGINATE_BY
  },
  DRAFT_LIST: {
    name: "DRAFT_LIST",
    rowNumber: PAGINATE_BY
  },
  NAVIGATION_LIST: {
    name: "NAVIGATION_LIST",
    rowNumber: PAGINATE_BY
  },
  ORDER_LIST: {
    name: "ORDER_LIST",
    rowNumber: PAGINATE_BY
  },
  PAGES_LIST: {
    name: "PAGES_LIST",
    rowNumber: PAGINATE_BY
  },
  PRODUCT_LIST: {
    name: "PRODUCT_LIST",
    rowNumber: PAGINATE_BY
  },
  SALES_LIST: {
    name: "SALES_LIST",
    rowNumber: PAGINATE_BY
  },
  SHIPPING_METHODS_LIST: {
    name: "SHIPPING_METHODS_LIST",
    rowNumber: PAGINATE_BY
  },
  STAFF_MEMBERS_LIST: {
    name: "COLLECTIOSTAFF_MEMBERS_LIST",
    rowNumber: PAGINATE_BY
  },
  VOUCHER_LIST: {
    name: "VOUCHER_LIST",
    rowNumber: PAGINATE_BY
  }
};
