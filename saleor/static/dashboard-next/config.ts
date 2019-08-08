import { SearchQueryVariables } from "./containers/BaseSearch";
import { ListSettings, ListViews } from "./types";

export const APP_MOUNT_URI = "/dashboard/next/";
export const API_URI = "/graphql/";

export const DEFAULT_INITIAL_SEARCH_DATA: SearchQueryVariables = {
  after: null,
  first: 5,
  query: ""
};

export const PAGINATE_BY = 20;

export type ProductListColumns = "productType" | "isPublished" | "price";
export interface AppListViewSettings {
  [ListViews.CATEGORY_LIST]: ListSettings;
  [ListViews.COLLECTION_LIST]: ListSettings;
  [ListViews.CUSTOMER_LIST]: ListSettings;
  [ListViews.DRAFT_LIST]: ListSettings;
  [ListViews.NAVIGATION_LIST]: ListSettings;
  [ListViews.ORDER_LIST]: ListSettings;
  [ListViews.PAGES_LIST]: ListSettings;
  [ListViews.PRODUCT_LIST]: ListSettings<ProductListColumns>;
  [ListViews.SALES_LIST]: ListSettings;
  [ListViews.SHIPPING_METHODS_LIST]: ListSettings;
  [ListViews.STAFF_MEMBERS_LIST]: ListSettings;
  [ListViews.VOUCHER_LIST]: ListSettings;
}
export const defaultListSettings: AppListViewSettings = {
  [ListViews.CATEGORY_LIST]: {
    rowNumber: PAGINATE_BY
  },
  [ListViews.COLLECTION_LIST]: {
    rowNumber: PAGINATE_BY
  },
  [ListViews.CUSTOMER_LIST]: {
    rowNumber: PAGINATE_BY
  },
  [ListViews.DRAFT_LIST]: {
    rowNumber: PAGINATE_BY
  },
  [ListViews.NAVIGATION_LIST]: {
    rowNumber: PAGINATE_BY
  },
  [ListViews.ORDER_LIST]: {
    rowNumber: PAGINATE_BY
  },
  [ListViews.PAGES_LIST]: {
    rowNumber: PAGINATE_BY
  },
  [ListViews.PRODUCT_LIST]: {
    columns: ["isPublished", "price", "productType"],
    rowNumber: PAGINATE_BY
  },
  [ListViews.SALES_LIST]: {
    rowNumber: PAGINATE_BY
  },
  [ListViews.SHIPPING_METHODS_LIST]: {
    rowNumber: PAGINATE_BY
  },
  [ListViews.STAFF_MEMBERS_LIST]: {
    rowNumber: PAGINATE_BY
  },
  [ListViews.VOUCHER_LIST]: {
    rowNumber: PAGINATE_BY
  }
};
