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
  PRODUCT_LIST: {
    name: "PRODUCT_LIST",
    rowNumber: PAGINATE_BY
  }
};
