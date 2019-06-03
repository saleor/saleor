import { SearchQueryVariables } from "./containers/BaseSearch";

export const APP_MOUNT_URI = "/dashboard/next/";
export const API_URI = "/graphql/";

export const DEFAULT_INITIAL_SEARCH_DATA: SearchQueryVariables = {
  after: null,
  first: 5,
  query: ""
};
