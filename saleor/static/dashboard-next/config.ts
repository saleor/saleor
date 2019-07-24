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
    rowNumber: PAGINATE_BY
  },
  COLLECTION_LIST: {
    rowNumber: PAGINATE_BY
  },
  CUSTOMER_LIST: {
    rowNumber: PAGINATE_BY
  },
  DRAFT_LIST: {
    rowNumber: PAGINATE_BY
  },
  NAVIGATION_LIST: {
    rowNumber: PAGINATE_BY
  },
  ORDER_LIST: {
    rowNumber: PAGINATE_BY
  },
  PAGES_LIST: {
    rowNumber: PAGINATE_BY
  },
  PRODUCT_LIST: {
    rowNumber: PAGINATE_BY
  },
  SALES_LIST: {
    rowNumber: PAGINATE_BY
  },
  SHIPPING_METHODS_LIST: {
    rowNumber: PAGINATE_BY
  },
  STAFF_MEMBERS_LIST: {
    rowNumber: PAGINATE_BY
  },
  VOUCHER_LIST: {
    rowNumber: PAGINATE_BY
  }
};
